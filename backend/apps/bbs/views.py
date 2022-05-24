from rest_framework.decorators import action
from django.db.models import Q

from .serializers import *
from message.models import Dynamic, MessageSetting, Like, Reply, Origin, At
from backend.libs.constants import response_code
from backend.libs.wraps.views import APIModelViewSet
from backend.libs.wraps.response import APIResponse
from backend.libs.wraps.authenticators import CommonJwtAuthentication, UserInfoAuthentication


class DraftView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    queryset = Draft.objects.filter(is_active=True)
    serializer_class = DraftSerializer
    code = {
        "create": response_code.SUCCESS_POST_DRAFT,
        "retrieve": response_code.SUCCESS_GET_DRAFT,
        "update": response_code.SUCCESS_EDIT_DRAFT,
        "list": response_code.SUCCESS_GET_DRAFT_LIST,
        "destroy": response_code.SUCCESS_DELETE_DRAFT,
    }

    def get_queryset(self):
        return self.queryset.filter(is_active=True, author=self.request.user, author__is_active=True).order_by(
            "-update_time")


class ArticleView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    queryset = Article.objects.filter(is_active=True)
    serializer_class = ArticleSerializer
    filter_fields = [
        "author",
        "author__id",
        "author__username",
        "category_id"
    ]
    ordering_fields = [
        "update_time",
        "create_time",
        "view_num",
        "up_num",
        "comment_num",
        "comment_time",
    ]
    search_fields = [
        "title",
        "author__id",
        "author__username",
        "category__category",
        "description",
        "content"
    ]
    code = {
        "create": response_code.SUCCESS_POST_ARTICLE,
        "retrieve": response_code.SUCCESS_GET_ARTICLE,
        "update": response_code.SUCCESS_EDIT_ARTICLE,
        "list": response_code.SUCCESS_GET_ARTICLE_LIST,
        "destroy": response_code.SUCCESS_DELETE_ARTICLE,
    }

    def get_authenticators(self):
        if self.request.method == "GET":
            return [UserInfoAuthentication()]

        return super().get_authenticators()

    def get_queryset(self):
        if self.action in ["retrieve", "list"]:
            return self.queryset.all()

        return self.queryset.filter(author=self.request.user, author__is_active=True).all()

    def after_retrieve(self, instance, request, *args, **kwargs):
        if not View.objects.filter(
                article=instance,
                name_id=request.user.id
        ).exists() and not request.user.is_anonymous:
            instance.view_num += 1
            instance.save()
            View.objects.create(article=instance, name_id=request.user.id)

    def before_create(self, request, *args, **kwargs):
        if not request.user.is_superuser and request.data.get("category_id") == 1:
            return APIResponse(response_code.NO_PERMISSION, "无权限")

    def after_create(self, instance, request, *args, **kwargs):
        a = request.user.follow_me.exclude(
            follower__message_setting__dynamic=0,
        ).filter(
            ~Q(follower_id__in=request.user.black_me_set)
        ).all()
        create_data = []
        for follow_record in a:
            create_data.append(Dynamic(
                sender=request.user,
                receiver=follow_record.follower,
                origin=Dynamic.BBS_ARTICLE,
                bbs_article=instance,
                is_viewed=follow_record.follower.message_setting.dynamic == MessageSetting.IGNORE,
            ))

        Dynamic.objects.bulk_create(create_data)

    def after_destroy(self, instance, request, *args, **kwargs):
        Dynamic.handle_delete(instance, Origin.BBS_ARTICLE)
        Like.handle_delete(instance, Origin.BBS_ARTICLE)
        Reply.handle_delete(instance, Origin.BBS_ARTICLE)
        At.handle_delete(instance, Origin.BBS_COMMENT)

    @action(["GET"], True)
    def raw(self, request, pk):
        query_set = self.get_queryset()
        if not query_set.filter(id=pk).exists():
            return APIResponse(response_code.INEXISTENT_ARTICLE, "文章不存在")

        instance = query_set.filter(id=pk).first()

        return APIResponse(response_code.SUCCESS_GET_ARTICLE, "成功获取文章信息", self.get_serializer(instance).data)

    @action(["POST"], True)
    def vote(self, request, pk):
        article = Article.objects.filter(id=pk, is_active=True)
        if not article:
            return APIResponse(response_code.INEXISTENT_ARTICLE, "文章不存在")

        article = article.first()
        data = request.data.copy()
        data["user_id"] = request.user.id
        data["article_id"] = pk

        ser = VoteArticleSerializer(data=data)
        ser.is_valid(True)
        ser.save()

        receiver = article.author
        sender = request.user
        if receiver != sender and receiver.message_setting.like != MessageSetting.FORBID:
            like = Like.objects.filter(bbs_article=article, sender=sender)
            if request.data.get("is_up") and not like:
                Like.objects.create(
                    origin=Like.BBS_ARTICLE,
                    bbs_article_id=pk,
                    sender=sender,
                    receiver=receiver,
                    is_viewed=receiver.is_viewed(sender, "like")
                )
            else:
                like = like.first()
                like.time = datetime.datetime.now()
                like.is_active = request.data.get("is_up") and not like.is_active
                like.save()

        return APIResponse(response_code.SUCCESS_VOTE_ARTICLE, "评价成功")


class CommentView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    queryset = Comment.objects.filter(is_active=True, parent_id=None, article__is_active=True)
    serializer_class = CommentSerializer
    filter_fields = ["author_id"]
    exclude = ["update", "retrieve"]
    ordering_fields = ["comment_time", "up_num", "comment_num"]
    code = {
        "create": response_code.SUCCESS_POST_COMMENT,
        "retrieve": response_code.SUCCESS_GET_COMMENT,
        "list": response_code.SUCCESS_GET_COMMENT_LIST,
        "destroy": response_code.SUCCESS_DELETE_COMMENT,
    }

    def get_authenticators(self):
        if self.request.method == "GET":
            return [UserInfoAuthentication()]

        return super().get_authenticators()

    def get_queryset(self):
        queryset = self.queryset.filter(article_id=self.kwargs.get("article_id"))
        if self.action in ["vote", "list"]:
            return queryset

        return queryset.filter(author=self.request.user)

    def after_create(self, instance: Comment, request, *args, **kwargs):
        instance.article.comment_num += 1
        instance.article.comment_time = datetime.datetime.now()
        instance.article.save()

        receiver = instance.article.author
        sender = request.user
        if receiver != sender and receiver.message_setting.reply != MessageSetting.FORBID:
            Reply.objects.create(
                origin=Reply.BBS_COMMENT,
                bbs_comment=instance,
                sender=sender,
                receiver=receiver,
                is_viewed=receiver.is_viewed(sender, "reply")
            )

    def after_destroy(self, instance: Comment, request, *args, **kwargs):
        instance.article.comment_num -= 1 + instance.comment_num
        instance.article.save()

        Dynamic.handle_delete(instance, Origin.BBS_COMMENT)
        Like.handle_delete(instance, Origin.BBS_COMMENT)
        Reply.handle_delete(instance, Origin.BBS_COMMENT)
        At.handle_delete(instance, Origin.BBS_COMMENT)

    @action(["POST"], True)
    def vote(self, request, article_id, pk):
        comment = Comment.objects.filter(article_id=article_id, article__is_active=True, id=pk, is_active=True)
        if not comment:
            return APIResponse(response_code.INEXISTENT_COMMENTS, "评论不存在")
        comment = comment.first()

        data = request.data.copy()
        data["user_id"] = request.user.id
        data["comment_id"] = pk
        ser = VoteCommentSerializer(data=data)
        ser.is_valid(True)
        ser.save()

        receiver = comment.author
        sender = request.user
        if receiver != sender and receiver.message_setting.like != MessageSetting.FORBID:
            like = Like.objects.filter(origin=Like.BBS_COMMENT, bbs_comment=comment, sender=sender)
            if request.data.get("is_up") and not like:
                Like.objects.create(
                    origin=Like.BBS_COMMENT,
                    bbs_comment_id=pk,
                    sender=sender,
                    receiver=receiver,
                    is_viewed=receiver.is_viewed(sender, "like")
                )
            else:
                like = like.first()
                like.time = datetime.datetime.now()
                like.is_active = request.data.get("is_up") and not like.is_active
                like.save()

        return APIResponse(response_code.SUCCESS_VOTE_COMMENT, "评价成功")


class ChildrenCommentView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    queryset = Comment.objects.filter(is_active=True, parent_id__isnull=False, parent__is_active=True,
                                      article__is_active=True)
    serializer_class = ChildrenCommentSerializer
    code = {
        "create": response_code.SUCCESS_POST_COMMENT,
        "retrieve": response_code.SUCCESS_GET_COMMENT,
        "list": response_code.SUCCESS_GET_COMMENT_LIST,
        "destroy": response_code.SUCCESS_DELETE_COMMENT,
    }

    def get_authenticators(self):
        if self.request.method == "GET":
            return [UserInfoAuthentication()]

        return super().get_authenticators()

    def get_queryset(self):
        order = self.request.query_params.get("order", "id")
        return self.queryset.filter(parent_id=self.kwargs.get("parent_id")).order_by(order).all()

    def before_create(self, request, *args, **kwargs):
        request.data["article_id"] = kwargs.pop("article_id", None)
        request.data["parent_id"] = kwargs.pop("parent_id", None)

    def after_create(self, instance: Comment, request, *args, **kwargs):
        instance.article.comment_num += 1
        instance.article.comment_time = datetime.datetime.now()
        instance.article.save()
        instance.parent.comment_num += 1
        instance.parent.save()

        if instance.target:
            receiver = instance.target.author
        else:
            receiver = instance.parent.author
        sender = request.user
        if receiver != sender and receiver.message_setting.reply != MessageSetting.FORBID:
            Reply.objects.create(
                origin=Reply.BBS_COMMENT,
                bbs_comment=instance,
                sender=sender,
                receiver=receiver,
                is_viewed=receiver.is_viewed(sender, "reply")
            )

    def after_destroy(self, instance: Comment, request, *args, **kwargs):
        instance.article.comment_num -= 1
        instance.article.save()
        instance.parent.comment_num -= 1
        instance.parent.save()

        Dynamic.handle_delete(instance, Origin.BBS_COMMENT)
        Like.handle_delete(instance, Origin.BBS_COMMENT)
        Reply.handle_delete(instance, Origin.BBS_COMMENT)
        At.handle_delete(instance, Origin.BBS_COMMENT)
