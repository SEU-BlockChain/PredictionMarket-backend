from .models import *
from user.models import User
from bbs.models import Article, Comment, UpAndDown, Category
from bbs.serializers import SimpleArticleSerializer
from backend.libs.wraps.serializers import APIModelSerializer, serializers
from backend.libs.wraps.errors import SerializerError
from backend.libs.constants import response_code


class AuthorSerializer(APIModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "icon",
            "username",
            "experience"
        ]


class DynamicCategorySerializer(APIModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class DynamicArticleSerializer(APIModelSerializer):
    author = AuthorSerializer()
    is_up = serializers.SerializerMethodField()
    category = DynamicCategorySerializer()

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
            "author",
            "title",
            "description",
            "category",
            "create_time",
            "category",
            "up_num",
            "view_num",
            "comment_num",
            "is_up"
        ]


class DynamicCommentSerializer(APIModelSerializer):
    author = AuthorSerializer()
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
            "author",
            "article",
            "content",
            "up_num",
            "down_num",
            "comment_num",
            "comment_time",
            "is_up"
        ]


class DynamicSerializer(APIModelSerializer):
    content = serializers.SerializerMethodField()

    def get_content(self, instance: Dynamic):
        if instance.origin == Dynamic.BBS_ARTICLE:
            content = DynamicArticleSerializer(instance.bbs_article, context=self.context).data
        elif instance.origin == Dynamic.BBS_COMMENT:
            content = DynamicCommentSerializer(instance.bbs_comment, context=self.context).data
        else:
            raise SerializerError(response_code.INVALID_PARAMS, "异常记录")
        return content

    class Meta:
        model = Dynamic
        fields = [
            "id",
            "origin",
            "content",
            "is_viewed"
        ]


class ReplyArticleSerializer(APIModelSerializer):
    class Meta:
        model = Article
        fields = [
            "id",
            "title",
        ]


class ReplySimpleSerializer(APIModelSerializer):
    author = AuthorSerializer()

    class Meta:
        model = Comment
        fields = [
            "id",
            "content",
            "author"
        ]


class ReplyCommentSerializer(APIModelSerializer):
    author = AuthorSerializer()
    article = ReplyArticleSerializer()
    parent = ReplySimpleSerializer()
    target = ReplySimpleSerializer()
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
            "author",
            "article",
            "comment_time",
            "content",
            "parent",
            "target",
            "is_up"
        ]


class ReplySerializer(APIModelSerializer):
    content = serializers.SerializerMethodField()

    def get_content(self, instance: Reply):
        if instance.origin == Reply.BBS_COMMENT:
            content = ReplyCommentSerializer(instance.bbs_comment, context=self.context).data
        else:
            raise SerializerError(response_code.INVALID_PARAMS, "异常记录")
        return content

    class Meta:
        model = Reply
        fields = [
            "id",
            "origin",
            "content",
            "is_viewed"
        ]
