from user.models import User
from .models import *
from backend.libs import *


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "icon"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = "__all__"


class ChildrenCommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    author_id = serializers.IntegerField(write_only=True)
    article_id = serializers.IntegerField(write_only=True)
    parent_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Comments
        fields = [
            "id",
            "author",
            "author_id",
            "article_id",
            "parent_id",
            "content",
            "up_num",
            "down_num",
            "comment_time",
        ]


class ArticleSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    author_id = serializers.IntegerField(write_only=True)
    category_id = serializers.IntegerField(write_only=True)

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
            "create_time",
            "update_time",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        action = self.context["view"].action
        self.context["action"] = action
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

    def update(self, instance: Articles, validated_data):
        if instance.author.id != validated_data.get("author_id"):
            raise SerializerError("无权限修改", response_code.NO_PERMISSION)

        return super().update(instance, validated_data)


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    children_comment = serializers.SerializerMethodField(read_only=True)
    author_id = serializers.IntegerField(write_only=True)
    article_id = serializers.IntegerField(write_only=True)

    def get_children_comment(self, instance: Comments):
        if children := instance.comments_set.all().order_by("-up_num")[:2]:
            return ChildrenCommentSerializer(children, many=True).data
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
        ]


__all__ = [
    "ArticleSerializer",
    "ChildrenCommentSerializer",
    "CommentSerializer",
]
