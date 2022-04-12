import re
from datetime import datetime

from lxml.etree import HTML
from django.db.models import F
from user.models import *
from .models import *
from backend.libs import *


class MetalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metal
        fields = "__all__"


class AuthorSerializer(serializers.ModelSerializer):
    metal = MetalSerializer(many=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "icon",
            "experience",
            "metal"
        ]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = "__all__"


class ChildrenCommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    author_id = serializers.IntegerField(write_only=True)
    article_id = serializers.IntegerField(write_only=True)
    parent_id = serializers.IntegerField(write_only=True)
    target_id = serializers.IntegerField(write_only=True)
    is_up = serializers.SerializerMethodField(read_only=True)

    def get_is_up(self, instance):
        if request := self.context.get("request"):
            author_id = request.user.id
            if not author_id:
                return None
            comment_id = instance.id
            obj = UpAndDowns.objects.filter(comment_id=comment_id, author_id=author_id).first()
            if not obj:
                return None

            return obj.is_up

    class Meta:
        model = Comments
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


class ArticleSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    author_id = serializers.IntegerField(write_only=True)
    category_id = serializers.IntegerField(write_only=True)
    is_up = serializers.SerializerMethodField(read_only=True)

    def get_is_up(self, instance):
        author_id = self.context["request"].user.id
        if not author_id:
            return None

        article_id = instance.id
        obj = UpAndDowns.objects.filter(article_id=article_id, author_id=author_id).first()
        if not obj:
            return None

        return obj.is_up

    class Meta:
        model = Articles
        fields = [
            "id",
            "title",
            "author",
            "author_id",
            "category",
            "category_id",
            "description",
            "content",
            "raw_content",
            "view_num",
            "up_num",
            "down_num",
            "comment_num",
            "create_time",
            "update_time",
            "is_up"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        action = self.context["view"].action
        self.context["action"] = action
        if action == "create":
            self.fields.pop("description")

        if action == "list":
            self.fields.pop("author_id")
            self.fields.pop("raw_content")
            self.fields.pop("category_id")
            self.fields.pop("content")

        if action == "update":
            self.fields.pop("category_id")
            self.fields.pop("raw_content")
            self.fields.pop("description")

        if action == "retrieve":
            self.fields.pop("raw_content")

        if action == "raw":
            self.fields.pop("category")
            self.fields.pop("category_id")
            self.fields.pop("content")
            self.fields.pop("description")

    def create(self, validated_data):
        validated_data["description"] = self.get_description(validated_data["content"])
        validated_data["update_time"] = datetime.now()
        return super().create(validated_data)

    def update(self, instance: Articles, validated_data):
        if instance.author.id != validated_data.get("author_id"):
            raise SerializerError("无权限修改", response_code.NO_PERMISSION)
        validated_data["description"] = self.get_description(validated_data["content"])

        return super().update(instance, validated_data)

    def get_description(self, content):
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


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    children_comment = serializers.SerializerMethodField(read_only=True)
    author_id = serializers.IntegerField(write_only=True)
    article_id = serializers.IntegerField(write_only=True)
    is_up = serializers.SerializerMethodField(read_only=True)

    def get_is_up(self, instance):
        author_id = self.context["request"].user.id
        if not author_id:
            return None

        comment_id = instance.id
        obj = UpAndDowns.objects.filter(comment_id=comment_id, author_id=author_id).first()
        if not obj:
            return None

        return obj.is_up

    def get_children_comment(self, instance: Comments):
        author_id = self.context["request"].user.id
        if children := instance.parent_comments.all().order_by("-up_num")[:2]:
            data = ChildrenCommentSerializer(children, many=True).data
            for i in data:
                if not author_id:
                    i["is_up"] = None
                else:
                    comment_id = i["id"]
                    obj = UpAndDowns.objects.filter(comment_id=comment_id, author_id=author_id).first()
                    if not obj:
                        i["is_up"] = None
                    else:
                        i["is_up"] = obj.is_up
            return data
        else:
            return []

    class Meta:
        model = Comments
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


class VoteArticleSerializer(EmptySerializer):
    article_id = serializers.CharField()
    user_id = serializers.CharField()
    is_up = serializers.ChoiceField([0, 1])

    def create(self, validated_data):
        article_id = validated_data.get("article_id")
        user_id = validated_data.get("user_id")
        is_up = validated_data.get("is_up")

        instance = UpAndDowns.objects.filter(article_id=article_id, author_id=user_id).first()

        if not instance:
            instance = UpAndDowns.objects.create(article_id=article_id, is_up=is_up, author_id=user_id)
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
        Articles.objects.filter(id=article_id).update(up_num=F("up_num") + up, down_num=F("down_num") + down)


class VoteCommentSerializer(EmptySerializer):
    comment_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    is_up = serializers.ChoiceField([0, 1])

    def create(self, validated_data):
        comment_id = validated_data.get("comment_id")
        user_id = validated_data.get("user_id")
        is_up = validated_data.get("is_up")
        instance = UpAndDowns.objects.filter(comment_id=comment_id, author_id=user_id).first()

        if not instance:
            instance = UpAndDowns.objects.create(comment_id=comment_id, is_up=is_up, author_id=user_id)
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
        Comments.objects.filter(id=comment_id).update(up_num=F("up_num") + up, down_num=F("down_num") + down)


__all__ = [
    "ArticleSerializer",
    "ChildrenCommentSerializer",
    "CommentSerializer",
    "VoteCommentSerializer",
    "VoteArticleSerializer",

    "AuthorSerializer"
]
