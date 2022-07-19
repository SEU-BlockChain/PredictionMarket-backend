from .models import *
from bbs import models as bbs_model
from bbs import serializers as bbs_serializers
from special import models as special_model
from special import serializers as special_serializer
from backend.libs.wraps.serializers import APIModelSerializer, serializers, SimpleAuthorSerializer
from backend.libs.wraps.errors import SerializerError
from backend.libs.constants import response_code


class MessageSettingSerializer(APIModelSerializer):
    class Meta:
        model = MessageSetting
        exclude = ["id"]


class DynamicBBSArticleSerializer(APIModelSerializer):
    author = SimpleAuthorSerializer()
    is_up = serializers.SerializerMethodField()
    category = bbs_serializers.CategorySerializer()

    def get_is_up(self, instance):
        author_id = self.context["request"].user.id
        if not author_id:
            return None

        article_id = instance.id
        obj = bbs_serializers.UpAndDown.objects.filter(article_id=article_id, author_id=author_id).first()
        if not obj:
            return None

        return obj.is_up

    class Meta:
        model = bbs_model.Article
        fields = [
            "id",
            "author",
            "title",
            "description",
            "create_time",
            "category",
            "up_num",
            "view_num",
            "comment_num",
            "is_up"
        ]


class DynamicBBSCommentSerializer(APIModelSerializer):
    author = SimpleAuthorSerializer()
    article = bbs_serializers.SimpleArticleSerializer()
    is_up = serializers.SerializerMethodField(read_only=True)

    def get_is_up(self, instance):
        author_id = self.context["request"].user.id
        if not author_id:
            return None

        comment_id = instance.id
        obj = bbs_model.UpAndDown.objects.filter(comment_id=comment_id, author_id=author_id).first()
        if not obj:
            return None

        return obj.is_up

    class Meta:
        model = bbs_model.Comment
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


class DynamicSpecialColumnSerializer(APIModelSerializer):
    author = SimpleAuthorSerializer()
    is_up = serializers.SerializerMethodField()
    tag = special_serializer.TagSerializer(many=True)

    def get_is_up(self, instance):
        author_id = self.context["request"].user.id
        if not author_id:
            return None

        column_id = instance.id
        obj = special_model.UpAndDown.objects.filter(column_id=column_id, author_id=author_id).first()
        if not obj:
            return None

        return obj.is_up

    class Meta:
        model = special_model.Column
        fields = [
            "id",
            "author",
            "title",
            "description",
            "tag",
            "create_time",
            "up_num",
            "view_num",
            "comment_num",
            "is_up"
        ]


class DynamicSpecialCommentSerializer(APIModelSerializer):
    author = SimpleAuthorSerializer()
    column = special_serializer.SimpleColumnSerializer()
    is_up = serializers.SerializerMethodField(read_only=True)

    def get_is_up(self, instance):
        author_id = self.context["request"].user.id
        if not author_id:
            return None

        comment_id = instance.id
        obj = special_model.UpAndDown.objects.filter(comment_id=comment_id, author_id=author_id).first()
        if not obj:
            return None

        return obj.is_up

    class Meta:
        model = bbs_model.Comment
        fields = [
            "author",
            "column",
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
        if instance.origin == Origin.BBS_ARTICLE:
            content = DynamicBBSArticleSerializer(instance.bbs_article, context=self.context).data
        elif instance.origin == Origin.BBS_COMMENT:
            content = DynamicBBSCommentSerializer(instance.bbs_comment, context=self.context).data
        elif instance.origin == Origin.SPECIAL_COLUMN:
            content = DynamicSpecialColumnSerializer(instance.special_column, context=self.context).data
        elif instance.origin == Origin.SPECIAL_COMMENT:
            content = DynamicSpecialCommentSerializer(instance.special_comment, context=self.context).data
        else:
            raise SerializerError("异常记录", response_code.INVALID_PARAMS)
        return content

    class Meta:
        model = Dynamic
        fields = [
            "id",
            "origin",
            "content",
            "is_viewed"
        ]


class ReplyBBSArticleSerializer(APIModelSerializer):
    author = SimpleAuthorSerializer()
    article = bbs_serializers.SimpleArticleSerializer()
    is_up = serializers.SerializerMethodField(read_only=True)

    def get_is_up(self, instance):
        author_id = self.context["request"].user.id
        if not author_id:
            return None

        comment_id = instance.id
        obj = bbs_model.UpAndDown.objects.filter(comment_id=comment_id, author_id=author_id).first()
        if not obj:
            return None

        return obj.is_up

    class Meta:
        model = bbs_model.Comment
        fields = [
            "id",
            "author",
            "article",
            "comment_time",
            "description",
            "is_up"
        ]


class ReplyBBSCommentSerializer(APIModelSerializer):
    author = SimpleAuthorSerializer()
    article = bbs_serializers.SimpleArticleSerializer()
    parent = bbs_serializers.SimpleCommentSerializer()
    target = bbs_serializers.SimpleCommentSerializer()
    is_up = serializers.SerializerMethodField(read_only=True)

    def get_is_up(self, instance):
        author_id = self.context["request"].user.id
        if not author_id:
            return None

        comment_id = instance.id
        obj = bbs_model.UpAndDown.objects.filter(comment_id=comment_id, author_id=author_id).first()
        if not obj:
            return None

        return obj.is_up

    class Meta:
        model = bbs_model.Comment
        fields = [
            "id",
            "author",
            "article",
            "comment_time",
            "description",
            "parent",
            "target",
            "is_up"
        ]


class ReplySpecialColumnSerializer(APIModelSerializer):
    author = SimpleAuthorSerializer()
    column = special_serializer.SimpleColumnSerializer()
    is_up = serializers.SerializerMethodField(read_only=True)

    def get_is_up(self, instance):
        author_id = self.context["request"].user.id
        if not author_id:
            return None

        comment_id = instance.id
        obj = special_model.UpAndDown.objects.filter(comment_id=comment_id, author_id=author_id).first()
        if not obj:
            return None

        return obj.is_up

    class Meta:
        model = special_model.Comment
        fields = [
            "id",
            "author",
            "column",
            "comment_time",
            "description",
            "is_up"
        ]


class ReplySpecialCommentSerializer(APIModelSerializer):
    author = SimpleAuthorSerializer()
    column = special_serializer.SimpleColumnSerializer()
    parent = special_serializer.SimpleCommentSerializer()
    target = special_serializer.SimpleCommentSerializer()
    is_up = serializers.SerializerMethodField(read_only=True)

    def get_is_up(self, instance):
        author_id = self.context["request"].user.id
        if not author_id:
            return None

        comment_id = instance.id
        obj = special_model.UpAndDown.objects.filter(comment_id=comment_id, author_id=author_id).first()
        if not obj:
            return None

        return obj.is_up

    class Meta:
        model = special_model.Comment
        fields = [
            "id",
            "author",
            "column",
            "comment_time",
            "description",
            "parent",
            "target",
            "is_up"
        ]


class ReplySerializer(APIModelSerializer):
    content = serializers.SerializerMethodField()

    def get_content(self, instance: Reply):
        if instance.origin == Origin.BBS_ARTICLE:
            content = ReplyBBSArticleSerializer(instance.bbs_comment, context=self.context).data
        elif instance.origin == Origin.BBS_COMMENT:
            content = ReplyBBSCommentSerializer(instance.bbs_comment, context=self.context).data
        elif instance.origin == Origin.SPECIAL_COLUMN:
            content = ReplySpecialColumnSerializer(instance.special_comment, context=self.context).data
        elif instance.origin == Origin.SPECIAL_COMMENT:
            content = ReplySpecialCommentSerializer(instance.special_comment, context=self.context).data
        else:
            raise SerializerError("异常记录", response_code.INVALID_PARAMS)
        return content

    class Meta:
        model = Reply
        fields = [
            "id",
            "origin",
            "content",
            "is_viewed"
        ]


class LikeBBSArticleSerializer(bbs_serializers.SimpleArticleSerializer):
    pass


class LikeBBSCommentSerializer(APIModelSerializer):
    article = bbs_serializers.SimpleArticleSerializer()

    class Meta:
        model = bbs_model.Comment
        fields = [
            "id",
            "description",
            "article"
        ]


class LikeSpecialColumnSerializer(special_serializer.SimpleColumnSerializer):
    pass


class LikeSpecialCommentSerializer(APIModelSerializer):
    column = LikeSpecialColumnSerializer()

    class Meta:
        model = special_model.Comment
        fields = [
            "id",
            "description",
            "column"
        ]


class LikeSerializer(APIModelSerializer):
    is_viewed = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    sender = SimpleAuthorSerializer()
    total = serializers.SerializerMethodField()
    new = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()

    def get_is_viewed(self, instance):
        return instance.viewed

    def get_content(self, instance: Like):
        if instance.origin == Origin.BBS_ARTICLE:
            content = LikeBBSArticleSerializer(instance.bbs_article).data
        elif instance.origin == Origin.BBS_COMMENT:
            content = LikeBBSCommentSerializer(instance.bbs_comment).data
        elif instance.origin == Origin.SPECIAL_COLUMN:
            content = LikeSpecialColumnSerializer(instance.special_column).data
        elif instance.origin == Origin.SPECIAL_COMMENT:
            content = LikeSpecialCommentSerializer(instance.special_comment).data
        else:
            raise SerializerError("异常记录", response_code.INVALID_PARAMS)
        return content

    def get_total(self, instance):
        return instance.total

    def get_new(self, instance):
        return int(instance.new)

    def get_time(self, instance):
        return instance.last_time

    class Meta:
        model = Like
        fields = [
            "id",
            "origin",
            "content",
            "sender",
            "is_viewed",
            "total",
            "new",
            "time"
        ]


class AtBBSArticleSerializer(APIModelSerializer):
    author = SimpleAuthorSerializer()

    class Meta:
        model = bbs_model.Article
        fields = [
            "id",
            "author",
            "title"
        ]


class AtBBSCommentSerializer(APIModelSerializer):
    author = SimpleAuthorSerializer()
    article = bbs_serializers.SimpleArticleSerializer()

    class Meta:
        model = bbs_model.Comment
        fields = [
            "id",
            "author",
            "article",
            "description"
        ]


class AtSpecialColumnSerializer(APIModelSerializer):
    author = SimpleAuthorSerializer()

    class Meta:
        model = special_model.Column
        fields = [
            "id",
            "author",
            "title"
        ]


class AtSpecialCommentSerializer(APIModelSerializer):
    author = SimpleAuthorSerializer()
    column = special_serializer.SimpleColumnSerializer()

    class Meta:
        model = special_model.Comment
        fields = [
            "id",
            "author",
            "column",
            "description"
        ]


class AtSerializer(APIModelSerializer):
    content = serializers.SerializerMethodField()

    def get_content(self, instance: At):
        if instance.origin == Origin.BBS_ARTICLE:
            content = AtBBSArticleSerializer(instance.bbs_article, context=self.context).data
        elif instance.origin == Origin.BBS_COMMENT:
            content = AtBBSCommentSerializer(instance.bbs_comment, context=self.context).data
        elif instance.origin == Origin.SPECIAL_COLUMN:
            content = AtSpecialColumnSerializer(instance.special_column, context=self.context).data
        elif instance.origin == Origin.SPECIAL_COMMENT:
            content = AtSpecialCommentSerializer(instance.special_comment, context=self.context).data
        else:
            raise SerializerError("异常记录", response_code.INVALID_PARAMS)
        return content

    class Meta:
        model = At
        fields = [
            "id",
            "origin",
            "content",
            "time",
            "is_viewed",
        ]


class SystemSerializer(APIModelSerializer):
    class Meta:
        model = System
        fields = [
            "id",
            "content",
            "time",
            "is_viewed",
        ]


class PrivateSerializer(APIModelSerializer):
    sender = SimpleAuthorSerializer()
    is_viewed = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    new = serializers.SerializerMethodField()

    def get_is_viewed(self, instance):
        return instance.viewed

    def get_time(self, instance):
        return instance.last_time

    def get_new(self, instance):
        return instance.new

    class Meta:
        model = Private
        fields = [
            "id",
            "content",
            "time",
            "is_viewed",
            "sender",
            "new"
        ]


class PrivateDetailSerializer(APIModelSerializer):
    class Meta:
        model = Private
        fields = [
            "id",
            "sender_id",
            "receiver_id",
            "content",
            "time",
            "is_viewed",
        ]

    def create(self, validated_data):
        validated_data["sender"] = self.context["request"].user
        validated_data["receiver_id"] = self.context["request"].query_params.get("uid")
        return super().create(validated_data)
