from rest_framework.decorators import action
from django.db.models import Q
from rest_framework.request import Request

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
        follower_list = request.user.follow_me.exclude(
            follower__message_setting__dynamic=0,
        ).filter(
            ~Q(follower_id__in=request.user.black_me_set)
        ).all()

        create_data = map(lambda follower: Dynamic(
            sender=request.user,
            receiver=follower.follower,
            origin=Origin.BBS_ARTICLE,
            bbs_article=instance,
            is_viewed=follower.follower.message_setting.dynamic == MessageSetting.IGNORE,
        ), follower_list)

        Dynamic.objects.bulk_create(create_data)

    def after_destroy(self, instance, request, *args, **kwargs):
        Dynamic.handle_delete(instance, Origin.BBS_ARTICLE)
        Like.handle_delete(instance, Origin.BBS_ARTICLE)
        Reply.handle_delete(instance, Origin.BBS_ARTICLE)
        At.handle_delete(instance, Origin.BBS_ARTICLE)

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
        if receiver != sender:
            if receiver.message_setting.like:

                like = Like.objects.filter(bbs_article=article, sender=sender)
                if request.data.get("is_up") and not like:
                    Like.objects.create(
                        origin=Origin.BBS_ARTICLE,
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
        if receiver != sender and receiver.message_setting.reply:
            Reply.objects.create(
                origin=Origin.BBS_ARTICLE,
                bbs_comment=instance,
                sender=sender,
                receiver=receiver,
                is_viewed=receiver.is_viewed(sender, "reply")
            )

        if request.data.get("share"):
            follower_list = request.user.follow_me.exclude(
                follower__message_setting__dynamic=0,
            ).filter(
                ~Q(follower_id__in=request.user.black_me_set)
            ).all()

            create_data = map(lambda follower: Dynamic(
                sender=request.user,
                receiver=follower.follower,
                origin=Origin.BBS_COMMENT,
                bbs_comment=instance,
                is_viewed=follower.follower.message_setting.dynamic == MessageSetting.IGNORE,
            ), follower_list)

            Dynamic.objects.bulk_create(create_data)

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
        if receiver != sender and receiver.message_setting.like:
            like = Like.objects.filter(origin=Origin.BBS_COMMENT, bbs_comment=comment, sender=sender)
            if request.data.get("is_up") and not like:
                Like.objects.create(
                    origin=Origin.BBS_COMMENT,
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

        receiver = instance.target.author if instance.target else instance.parent.author
        sender = request.user

        if receiver != sender and receiver.message_setting.reply:
            Reply.objects.create(
                origin=Origin.BBS_COMMENT,
                bbs_comment=instance,
                sender=sender,
                receiver=receiver,
                is_viewed=receiver.is_viewed(sender, "reply")
            )

        if request.data.get("share"):
            follower_list = request.user.follow_me.exclude(
                follower__message_setting__dynamic=0,
            ).filter(
                ~Q(follower_id__in=request.user.black_me_set)
            ).all()

            create_data = map(lambda follower: Dynamic(
                sender=request.user,
                receiver=follower.follower,
                origin=Origin.BBS_COMMENT,
                bbs_comment=instance,
                is_viewed=follower.follower.message_setting.dynamic == MessageSetting.IGNORE,
            ), follower_list)

            Dynamic.objects.bulk_create(create_data)

    def after_destroy(self, instance: Comment, request, *args, **kwargs):
        instance.article.comment_num -= 1
        instance.article.save()
        instance.parent.comment_num -= 1
        instance.parent.save()

        Dynamic.handle_delete(instance, Origin.BBS_COMMENT)
        Like.handle_delete(instance, Origin.BBS_COMMENT)
        Reply.handle_delete(instance, Origin.BBS_COMMENT)
        At.handle_delete(instance, Origin.BBS_COMMENT)


class CategoryView(APIModelViewSet):
    authentication_classes = [UserInfoAuthentication]
    queryset = Category.objects.all().order_by("top")
    serializer_class = CategorySerializer
    exclude = ["destroy", "create", "update"]
    code = {
        "list": response_code.SUCCESS_LIST_BBS_CATEGORY,
        "retrieve": response_code.SUCCESS_GET_BBS_CATEGORY
    }

    def get_queryset(self):
        if self.action == "list" and self.request.query_params.get("type") == "edit" and not self.request.user.is_staff:
            return self.queryset.filter(stuff=False)

        return super().get_queryset()


class CollectionView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    queryset = Collection.objects.filter(is_active=True).all()
    serializer_class = CollectionSerializer
    code = {
        "list": response_code.SUCCESS_GET_COLLECTION_LIST,
        "retrieve": response_code.SUCCESS_GET_COLLECTION,
        "destroy": response_code.SUCCESS_DELETE_COLLECTION,
        "create": response_code.SUCCESS_POST_COLLECTION,
        "update": response_code.SUCCESS_EDIT_COLLECTION
    }

    def get_queryset(self):
        return self.queryset.filter(author=self.request.user).order_by("-create_time")


class CollectionInfoView(APIModelViewSet):
    authentication_classes = [UserInfoAuthentication]
    exclude = ["list", "destroy", "create", "update"]
    queryset = Collection.objects.filter(is_active=True).all()
    serializer_class = CollectionInfoSerializer
    code = {
        "list": response_code.SUCCESS_GET_COLLECTION
    }

    def list(self, request, *args, **kwargs):
        collection = self.queryset.filter(id=kwargs.get("collection_id"))
        if not collection:
            return APIResponse(response_code.INEXISTENT_COLLECTION, "合集不存在")

        return APIResponse(
            self.code["list"],
            result=self.serializer_class(
                collection.first(),
                context={"user": request.user}
            ).data
        )


class CollectionArticleView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    queryset = CollectionToArticle
    serializer_class = CollectionArticleSerializer
    exclude = ["retrieve", "update"]
    code = {
        "list": response_code.SUCCESS_GET_COLLECTION_LIST,
        "destroy": response_code.SUCCESS_DELETE_COLLECTION,
        "create": response_code.SUCCESS_POST_COLLECTION,
    }

    def get_authenticators(self):
        if self.request.method == "GET":
            return [UserInfoAuthentication()]

        return super().get_authenticators()

    def get_queryset(self):
        return self.queryset.objects.filter(
            collection_id=self.kwargs.get("collection_id"),
            collection__is_active=True,
            is_active=True, article__is_active=True
        ).all().order_by("top")

    def create(self, request: Request, *args, **kwargs):
        collection = Collection.objects.filter(id=self.kwargs.get("collection_id"))
        if not collection:
            return APIResponse(response_code.INEXISTENT_COLLECTION, "合集不存在")

        collection = collection.first()

        article = Article.objects.filter(author=request.user, is_active=True, id=request.data.get("article_id"))

        if not article:
            return APIResponse(response_code.INEXISTENT_ARTICLE, "文章不存在")

        article = article.first()

        if collection in article.collection_set.filter(collectiontoarticle__is_active=True).all():
            return APIResponse(response_code.ALREADY_IN_COLLECTION, "文章已在该合集中")

        total = CollectionToArticle.objects.filter(collection=collection, is_active=True).count()
        CollectionToArticle.objects.create(article=article, top=total + 1, collection=collection)
        return APIResponse(self.code["create"], "已添加到合集")

    def destroy(self, request, *args, **kwargs):
        collection = Collection.objects.filter(id=self.kwargs.get("collection_id"))

        if not collection:
            return APIResponse(response_code.INEXISTENT_COLLECTION, "合集不存在")

        collection = collection.first()

        article = CollectionToArticle.objects.filter(collection=collection, is_active=True, article_id=kwargs.get("pk"))

        if not article:
            return APIResponse(response_code.INEXISTENT_ARTICLE, "文章不存在")

        article = article.first()

        article.is_active = False
        article.save()
        return APIResponse(self.code["destroy"], "已移出合集")
