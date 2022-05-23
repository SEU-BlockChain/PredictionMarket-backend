import re
from datetime import datetime

from lxml.etree import HTML
from django.db.models import F

from .models import *
from backend.libs.wraps.serializers import EmptySerializer, serializers, APIModelSerializer, OtherUserSerializer
from backend.libs.wraps.errors import SerializerError
from backend.libs.constants import response_code


class CategorySerializer(APIModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class DraftSerializer(APIModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Draft
        fields = [
            "id",
            "title",
            "category",
            "category_id",
            "update_time",
            "raw_content",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        action = self.context["view"].action
        self.context["action"] = action
        remove = []
        if action == "list":
            remove = [
                "category_id",
                "raw_content"
            ]
        if action == "retrieve":
            remove = [
                "category_id",
                "update_time"
            ]

        for i in remove:
            self.fields.pop(i)

    def create(self, validated_data):
        validated_data["author_id"] = self.context["request"].user.id
        return super().create(validated_data)


class ArticleSerializer(APIModelSerializer):
    author = OtherUserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    is_up = serializers.SerializerMethodField(read_only=True)

    def get_is_up(self, instance):
        author_id = self.context["request"].user.id
        if not author_id:
            return None

        article_id = instance.id
        obj = UpAndDown.objects.filter(article_id=article_id, author_id=author_id).first()
        if not obj:
            return None

        return obj.is_up

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "author",
            "category",
            "category_id",
            "description",
            "content",
            "raw_content",
            "view_num",
            "up_num",
            "down_num",
            "comment_num",
            "comment_time",
            "create_time",
            "update_time",
            "is_up"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        action = self.context["view"].action
        self.context["action"] = action
        remove = []
        if action == "create":
            remove = [
                "description",
                "author",
                "category",
                "view_num",
                "up_num",
                "down_num",
                "comment_num",
                "create_time",
                "update_time",
                "is_up"
            ]

        if action == "list":
            remove = [
                "category_id",
                "content",
                "raw_content"
            ]

        if action == "update":
            remove = [
                "author",
                "category",
                "category_id",
                "description",
                "view_num",
                "up_num",
                "down_num",
                "comment_num",
                "create_time",
                "update_time",
                "is_up"
            ]

        if action == "retrieve":
            remove = [
                "category_id",
                "description",
                "raw_content",
            ]

        if action == "raw":
            remove = [
                "author",
                "category_id",
                "description",
                "content",
                "view_num",
                "up_num",
                "down_num",
                "comment_num",
                "create_time",
                "update_time",
                "is_up"
            ]

        for i in remove:
            self.fields.pop(i)

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        validated_data["description"] = self._get_description(validated_data["content"])
        return super().create(validated_data)

    def update(self, instance: Article, validated_data):
        validated_data["description"] = self._get_description(validated_data["content"])
        validated_data["update_time"] = datetime.datetime.now()
        return super().update(instance, validated_data)

    def _get_description(self, content):
        text = HTML(content).xpath("string(.)")
        if len(text) <= 64:
            html_text = f'<div>{text}</div>'
        else:
            html_text = f'<div>{text[:64]}...</div>'

        img_urls = re.findall('<img src="(.*?)" .*?/>', content)

        if not img_urls:
            return html_text

        img_url = img_urls[0]
        html_image = f'<img src="{img_url}"/>'
        return html_text + html_image


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
            "article_id",
            "is_up"
        ]

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        validated_data["article_id"] = self.context["kwargs"].get("article_id")
        validated_data["description"] = self._get_description(validated_data["content"])
        return super().create(validated_data)

    def _get_description(self, content):
        text = HTML(content).xpath("string(.)")
        if len(text) <= 40:
            html_text = f'<span>{text}</span>'
        else:
            html_text = f'<span>{text[:40]}...</span>'

        img_urls = re.findall('<img src="(.*?)" .*?/>', content)

        if not img_urls:
            return html_text

        return html_text + "<span>[图片]</span>"


class SimpleArticleSerializer(APIModelSerializer):
    class Meta:
        model = Article
        fields = [
            "id",
            "title"
        ]


class SelfCommentSerializer(APIModelSerializer):
    article = SimpleArticleSerializer()
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

    class Meta:
        model = Comment
        fields = [
            "id",
            "content",
            "up_num",
            "down_num",
            "comment_num",
            "comment_time",
            "article",
            "is_up"
        ]


class ChildrenCommentSerializer(APIModelSerializer):
    author = OtherUserSerializer(read_only=True)
    article_id = serializers.IntegerField(write_only=True)
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
            "article_id",
            "parent_id",
            "target_id",
            "content",
            "up_num",
            "down_num",
            "comment_time",
            "is_up",
        ]

    def create(self, validated_data):
        content = validated_data["content"]
        validated_data["description"] = self._get_description(validated_data["content"])

        if validated_data.get("target_id"):
            validated_data["content"], prefix = self._add_mention(content, validated_data)
            validated_data["description"] = prefix + validated_data["description"]
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)

    def _add_mention(self, content, validated_data):
        article_id = validated_data["article_id"]
        parent_id = validated_data["parent_id"]
        target_id = validated_data["target_id"]
        comment = Comment.objects.filter(
            id=target_id,
            article_id=article_id,
            parent_id=parent_id
        )
        if not comment:
            raise SerializerError("评论不存在", response_code.NOT_FOUND)
        comment = comment.first()
        content = "".join([
            content[:3],
            f'回复&nbsp;<span style="color: rgb(54, 88, 226);">@{comment.author.username}:</span>',
            content[3:]
        ])
        return content, f'回复&nbsp;<span style="color: rgb(54, 88, 226);">@{comment.author.username}:</span>'

    def _get_description(self, content):
        text = HTML(content).xpath("string(.)")
        if len(text) <= 40:
            html_text = f'<span>{text}</span>'
        else:
            html_text = f'<span>{text[:40]}...</span>'

        img_urls = re.findall('<img src="(.*?)" .*?/>', content)

        if not img_urls:
            return html_text

        return html_text + "<span>[图片]</span>"


class VoteArticleSerializer(EmptySerializer):
    article_id = serializers.CharField()
    user_id = serializers.CharField()
    is_up = serializers.ChoiceField([0, 1])

    def create(self, validated_data):
        article_id = validated_data.get("article_id")
        user_id = validated_data.get("user_id")
        is_up = validated_data.get("is_up")

        instance = UpAndDown.objects.filter(article_id=article_id, author_id=user_id).first()

        if not instance:
            instance = UpAndDown.objects.create(article_id=article_id, is_up=is_up, author_id=user_id)
            self._update_num(article_id, is_up, 1 - is_up)
        else:
            if instance.is_up == is_up:
                instance.delete()
                self._update_num(article_id, -is_up, is_up - 1)
            else:
                instance.is_up = is_up
                instance.save()
                self._update_num(article_id, 2 * is_up - 1, 1 - 2 * is_up)

        return instance

    @staticmethod
    def _update_num(article_id, up, down):
        Article.objects.filter(id=article_id).update(up_num=F("up_num") + up, down_num=F("down_num") + down)


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
