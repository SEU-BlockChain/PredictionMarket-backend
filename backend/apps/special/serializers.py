import re
from datetime import datetime

from lxml import etree
from django.db.models import F

from .models import *
from user.models import User
from backend.libs.wraps.serializers import EmptySerializer, serializers, APIModelSerializer, OtherUserSerializer, \
    SimpleAuthorSerializer
from backend.libs.wraps.errors import SerializerError
from backend.libs.constants import response_code


class TagSerializer(APIModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class MyColumnSerializer(APIModelSerializer):
    tag = TagSerializer(many=True, read_only=True)
    tag_list = serializers.ListField(write_only=True)

    class Meta:
        model = Column
        fields = [
            "id",
            "title",
            "description",
            "content",
            "raw_content",
            "tag",
            "tag_list",
            "menu",
            "update_time",
            "is_draft",
            "is_audit",
        ]
        extra_kwargs = {
            "content": {"required": False}
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        action = self.context["view"].action
        self.context["action"] = action
        remove = []
        if action == "list":
            remove = [
                "menu",
                "tag",
                "description",
                "raw_content",
                "content"
            ]
        if action == "retrieve":
            remove = [
                "update_time",
                "menu",
                "content",
            ]
        if action == "create":
            remove = [
                "update_time",
                "is_audit",
            ]
        if action == "update":
            remove = [
                "update_time",
                "is_audit",
            ]
        for i in remove:
            self.fields.pop(i)

    def create(self, validated_data):
        validated_data["is_audit"] = True
        validated_data["author_id"] = self.context["request"].user.id
        tag_list = validated_data.pop("tag_list")
        instance: Column = super().create(validated_data)
        ColumnToTag.objects.bulk_create(map(lambda x: ColumnToTag(column_id=instance.id, tag_id=x["id"]), tag_list))
        return instance

    def update(self, instance, validated_data):
        validated_data["is_audit"] = True
        validated_data["update_time"] = datetime.datetime.now()
        instance: Column = super().update(instance, validated_data)
        ColumnToTag.objects.filter(column=instance).delete()
        tag_list = validated_data.pop("tag_list")
        ColumnToTag.objects.bulk_create(map(lambda x: ColumnToTag(column_id=instance.id, tag_id=x["id"]), tag_list))
        return instance


class ColumnSerializer(APIModelSerializer):
    author = OtherUserSerializer(read_only=True)
    tag = TagSerializer(many=True, read_only=True)
    is_up = serializers.SerializerMethodField(read_only=True)

    def get_is_up(self, instance):
        author_id = self.context["request"].user.id
        if not author_id:
            return None

        column_id = instance.id
        obj = UpAndDown.objects.filter(column_id=column_id, author_id=author_id).first()
        if not obj:
            return None

        return obj.is_up

    class Meta:
        model = Column
        fields = [
            "id",
            "author",
            "title",
            "description",
            "content",
            "menu",
            "tag",
            "is_up",
            "comment_time",
            "update_time",
            "create_time",
            "comment_num",
            "view_num",
            "up_num",
            "down_num",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        action = self.context["view"].action
        self.context["action"] = action
        remove = []
        if action == "list":
            remove = [
                "menu",
                "update_time",
                "content",
                "create_time",
                "down_num"
            ]
        if action == "retrieve":
            remove = [
                "comment_time",
            ]
        for i in remove:
            self.fields.pop(i)


class VoteColumnSerializer(EmptySerializer):
    column_id = serializers.CharField()
    user_id = serializers.CharField()
    is_up = serializers.ChoiceField([0, 1])

    def create(self, validated_data):
        column_id = validated_data.get("column_id")
        user_id = validated_data.get("user_id")
        is_up = validated_data.get("is_up")

        instance = UpAndDown.objects.filter(column_id=column_id, author_id=user_id).first()
        receiver = Column.objects.get(id=column_id).author

        if not instance:
            if is_up:
                receiver.up_num += 1
            instance = UpAndDown.objects.create(column_id=column_id, is_up=is_up, author_id=user_id)
            self._update_num(column_id, is_up, 1 - is_up)
        else:
            if instance.is_up == is_up:
                receiver.up_num -= is_up
                instance.delete()
                self._update_num(column_id, -is_up, is_up - 1)
            else:
                instance.is_up = is_up
                receiver.up_num += 2 * is_up - 1
                instance.save()
                self._update_num(column_id, 2 * is_up - 1, 1 - 2 * is_up)

        receiver.save()
        return instance

    @staticmethod
    def _update_num(column_id, up, down):
        Column.objects.filter(id=column_id).update(up_num=F("up_num") + up, down_num=F("down_num") + down)


class CommentSerializer(APIModelSerializer):
    author = OtherUserSerializer(read_only=True)
    children_comment = serializers.SerializerMethodField(read_only=True)
    is_up = serializers.SerializerMethodField(read_only=True)

    def get_is_up(self, instance):
        author_id = self.context["request"].user.id
        if not author_id:
            return None

        comment_id = instance.id
        obj = UpAndDown.objects.filter(comment_id=comment_id, author_id=author_id).first()
        if not obj:
            return None

        return obj.is_up

    def get_children_comment(self, instance: Comment):
        author_id = self.context["request"].user.id
        if children := instance.parent_comments.all().filter(is_active=True).order_by("-up_num")[:2]:
            data = ChildrenCommentSerializer(children, many=True, context=self.context).data
            for i in data:
                if not author_id:
                    i["is_up"] = None
                else:
                    comment_id = i["id"]
                    obj = UpAndDown.objects.filter(comment_id=comment_id, author_id=author_id).first()
                    if not obj:
                        i["is_up"] = None
                    else:
                        i["is_up"] = obj.is_up
            return data
        else:
            return []

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "author_id",
            "content",
            "up_num",
            "down_num",
            "comment_num",
            "comment_time",
            "children_comment",
            "column_id",
            "is_up"
        ]

    def create(self, validated_data):
        validated_data["content"] = self._add_mention(validated_data["content"])
        validated_data["author"] = self.context["request"].user
        validated_data["column_id"] = self.context["kwargs"].get("column_id")
        validated_data["description"] = self._get_description(validated_data["content"])
        return super().create(validated_data)

    def _get_description(self, content):
        text = etree.HTML(content).xpath("string(.)")
        if len(text) <= 40:
            html_text = f'<span>{text}</span>'
        else:
            html_text = f'<span>{text[:40]}...</span>'

        img_urls = re.findall('<img src="(.*?)" .*?/>', content)

        if not img_urls:
            return html_text

        return html_text + "<span>[图片]</span>"

    def _add_mention(self, html):
        self.context["mention"] = []
        tree = etree.HTML(html)
        for i in tree.xpath("//span[@data-w-e-type='mention']"):
            uid = i.xpath("@data-info")[0]
            username = i.xpath("text()")[0].replace("@", "")
            user = User.objects.filter(id=uid, username=username)
            if user:
                self.context["mention"].append(user.first())
                i.set("style", "color: rgb(54, 88, 226);")
                i.set("uid", uid)

        return etree.tostring(tree).decode("utf-8")[12:-14]


class ChildrenCommentSerializer(APIModelSerializer):
    author = OtherUserSerializer(read_only=True)
    column_id = serializers.IntegerField(write_only=True)
    parent_id = serializers.IntegerField(write_only=True)
    target_id = serializers.IntegerField(allow_null=True, default=None)
    is_up = serializers.SerializerMethodField(read_only=True)

    def get_is_up(self, instance):
        if request := self.context.get("request"):
            author_id = request.user.id
            if not author_id:
                return None
            comment_id = instance.id
            obj = UpAndDown.objects.filter(comment_id=comment_id, author_id=author_id).first()
            if not obj:
                return None

            return obj.is_up

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "author_id",
            "column_id",
            "parent_id",
            "target_id",
            "content",
            "up_num",
            "down_num",
            "comment_time",
            "is_up",
        ]

    def create(self, validated_data):
        if validated_data.get("target_id"):
            validated_data["content"] = self._add_mention_prefix(validated_data["content"], validated_data)

        validated_data["content"] = self._add_mention(validated_data["content"])
        validated_data["description"] = self._get_description(validated_data["content"])
        validated_data["author"] = self.context["request"].user

        return super().create(validated_data)

    def _add_mention_prefix(self, content, validated_data):
        column_id = validated_data["column_id"]
        parent_id = validated_data["parent_id"]
        target_id = validated_data["target_id"]
        comment = Comment.objects.filter(
            id=target_id,
            column_id=column_id,
            parent_id=parent_id
        )
        if not comment:
            raise SerializerError("评论不存在", response_code.NOT_FOUND)
        comment = comment.first()
        content = "".join([
            content[:3],
            f'回复&nbsp;<span style="color: rgb(54, 88, 226);" uid="{comment.author.id}">@{comment.author.username}:</span>',
            content[3:]
        ])
        return content

    def _get_description(self, content):
        text = etree.HTML(content).xpath("string(.)")
        if len(text) <= 40:
            html_text = f'<span>{text}</span>'
        else:
            html_text = f'<span>{text[:40]}...</span>'

        img_urls = re.findall('<img src="(.*?)" .*?/>', content)

        if not img_urls:
            return html_text

        return html_text + "<span>[图片]</span>"

    def _add_mention(self, html):
        self.context["mention"] = []
        tree = etree.HTML(html)
        for i in tree.xpath("//span[@data-w-e-type='mention']"):
            uid = i.xpath("@data-info")[0]
            username = i.xpath("text()")[0].replace("@", "")
            user = User.objects.filter(id=uid, username=username)
            if user:
                self.context["mention"].append(user.first())
                i.set("style", "color: rgb(54, 88, 226);")
                i.set("uid", uid)

        return etree.tostring(tree).decode("utf-8")[12:-14]


class VoteCommentSerializer(EmptySerializer):
    comment_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    is_up = serializers.ChoiceField([0, 1])

    def create(self, validated_data):
        comment_id = validated_data.get("comment_id")
        user_id = validated_data.get("user_id")
        is_up = validated_data.get("is_up")

        instance = UpAndDown.objects.filter(comment_id=comment_id, author_id=user_id).first()

        if not instance:
            instance = UpAndDown.objects.create(comment_id=comment_id, is_up=is_up, author_id=user_id)
            self._update_num(comment_id, is_up, 1 - is_up)
        else:
            if instance.is_up == is_up:
                instance.delete()
                self._update_num(comment_id, -is_up, is_up - 1)
            else:
                instance.is_up = is_up
                instance.save()
                self._update_num(comment_id, 2 * is_up - 1, 1 - 2 * is_up)

        return instance

    @staticmethod
    def _update_num(comment_id, up, down):
        Comment.objects.filter(id=comment_id).update(up_num=F("up_num") + up, down_num=F("down_num") + down)


class SimpleColumnSerializer(APIModelSerializer):
    class Meta:
        model = Column
        fields = [
            "id",
            "title"
        ]


class SimpleCommentSerializer(APIModelSerializer):
    author = SimpleAuthorSerializer()

    class Meta:
        model = Comment
        fields = [
            "id",
            "description",
            "author"
        ]


class SelfCommentSerializer(APIModelSerializer):
    column = SimpleColumnSerializer()
    is_up = serializers.SerializerMethodField(read_only=True)
    target = SimpleCommentSerializer()
    parent = SimpleCommentSerializer()

    def get_is_up(self, instance):
        author_id = self.context["request"].user.id
        if not author_id:
            return None

        comment_id = instance.id
        obj = UpAndDown.objects.filter(comment_id=comment_id, author_id=author_id).first()
        if not obj:
            return None

        return obj.is_up

    class Meta:
        model = Comment
        fields = [
            "id",
            "content",
            "up_num",
            "down_num",
            "target",
            "parent",
            "comment_num",
            "comment_time",
            "column",
            "is_up"
        ]
