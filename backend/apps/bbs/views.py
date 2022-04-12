from rest_framework.decorators import action
from .models import *
from .serializers import *
from backend.libs import *
from user.models import *


class ArticleView(APIModelViewSet):
    http_method_names = ['get', 'post', 'patch', "delete", 'head', 'options', 'trace']
    authentication_classes = [CommonJwtAuthentication]
    queryset = Articles.objects.filter(is_active=True)
    serializer_class = ArticleSerializer
    filter_fields = ["author", "author__username", "category", "category__category"]
    search_fields = [
        "title",
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
        order = self.request.query_params.get("order", "-update_time")
        return self.queryset.order_by(order).all()

    def retrieve(self, request, *args, **kwargs):
        article_id = kwargs.get("pk")
        article = self.get_queryset().filter(id=article_id).first()
        if not article:
            return APIResponse(response_code.INEXISTENT_ARTICLE, "文章不存在")

        if not Views.objects.filter(article_id=article_id, name_id=request.user.id).exists() and request.user.id:
            article.view_num += 1
            article.save()
            Views.objects.create(article_id=article_id, name_id=request.user.id)

        serializer = self.get_serializer(article)

        return APIResponse(self.code["retrieve"], "成功获取单条数据", serializer.data)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["author_id"] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(True)

        self.perform_create(serializer)

        return APIResponse(self.code["create"], "成功添加数据", serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        data["author_id"] = request.user.id
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(True)

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return APIResponse(self.code["update"], "已更新", serializer.data)

    def destroy(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        pk = kwargs.get("pk")
        if not queryset.filter(id=pk).exists():
            return APIResponse(response_code.INEXISTENT_ARTICLE, "文章不存在")

        if not queryset.filter(id=pk, author=request.user).exists():
            return APIResponse(response_code.NO_PERMISSION, "没有权限")

        instance = queryset.filter(id=pk, author=request.user).first()
        instance.is_active = False
        instance.save()

        return APIResponse(self.code["destroy"], "文章已删除")

    @action(["GET"], True)
    def raw(self, request, pk):
        query_set = self.get_queryset()
        if not query_set.filter(id=pk).exists():
            return APIResponse(response_code.INEXISTENT_ARTICLE, "文章不存在")

        instance = query_set.filter(id=pk).first()
        if request.user.id != instance.author.id:
            return APIResponse(response_code.NO_PERMISSION, "无权限修改")

        return APIResponse(response_code.SUCCESS_GET_ARTICLE, "成功获取文章信息", self.get_serializer(instance).data)

    @action(["POST"], True)
    def vote(self, request, pk):
        if not Articles.objects.filter(id=pk, is_active=True).exists():
            return APIResponse(response_code.INEXISTENT_ARTICLE, "文章不存在")

        data = request.data.copy()
        data["user_id"] = request.user.id
        data["article_id"] = pk

        ser = VoteArticleSerializer(data=data)
        ser.is_valid(True)
        ser.save()

        return APIResponse(response_code.SUCCESS_VOTE_ARTICLE, "评价成功")

    @action(["GET"], True)
    def recommend(self, request, pk):
        author_id = Articles.objects.filter(id=pk).first().author.id
        if not author_id:
            return APIResponse(response_code.INVALID_PARAMS, "缺少参数")

        data = Articles.objects.filter(
            is_active=True,
            author_id=author_id
        ).exclude(id=pk).order_by("-up_num")[:10].values("title", "id")

        return APIResponse(response_code.SUCCESS_GET_RECOMMEND, "成功获取推荐", data)


class CommentView(APIModelViewSet):
    http_method_names = ['get', 'post', "delete", 'head', 'options', 'trace']
    authentication_classes = [CommonJwtAuthentication]
    queryset = Comments.objects.filter(is_active=True, parent_id=None, article__is_active=True)
    serializer_class = CommentSerializer
    filter_fields = ["author"]
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
        order = self.request.query_params.get("order", "-id")
        return self.queryset.filter(article_id=self.kwargs.get("article_id")).order_by(order).all()

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["author_id"] = request.user.id
        data["article_id"] = article_id = kwargs.get("article_id")
        data["content"] = request.data.get("content")

        serializer = self.get_serializer(data=data)
        serializer.is_valid(True)

        instance = serializer.save()
        BBSReply.objects.create(comment=instance, is_article=True)
        article = Articles.objects.filter(id=article_id, is_active=True).first()
        article.comment_num += 1
        article.save()

        return APIResponse(self.code["create"], "成功添加数据", serializer.data)

    def destroy(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        article_id = kwargs.get("article_id")
        comment_id = kwargs.get("pk")
        if not queryset.filter(id=comment_id, article_id=article_id).exists():
            return APIResponse(response_code.INEXISTENT_COMMENTS, "评论不存在")

        if not queryset.filter(id=comment_id, article_id=article_id, author_id=request.user).exists():
            return APIResponse(response_code.NO_PERMISSION, "没有权限")

        instance = queryset.filter(id=comment_id, article_id=article_id, author_id=request.user).first()
        instance.is_active = False
        instance.save()

        return APIResponse(self.code["destroy"], "评论已删除")

    def retrieve(self, request, *args, **kwargs):
        return APIResponse(response_code.METHOD_NOT_ALLOWED, "无效的请求方式")

    @action(["POST"], True)
    def vote(self, request, article_id, pk):
        if not Comments.objects.filter(article_id=article_id, article__is_active=True, id=pk, is_active=True).exists():
            return APIResponse(response_code.INEXISTENT_COMMENTS, "评论不存在")

        data = request.data.copy()
        data["user_id"] = request.user.id
        data["comment_id"] = pk
        ser = VoteCommentSerializer(data=data)
        ser.is_valid(True)
        ser.save()

        return APIResponse(response_code.SUCCESS_VOTE_COMMENT, "评价成功")


class ChildrenCommentView(APIModelViewSet):
    http_method_names = ['get', 'post', "delete", 'head', 'options', 'trace']
    authentication_classes = [CommonJwtAuthentication]
    queryset = Comments.objects.filter(is_active=True, parent_id__isnull=False, parent__is_active=True,
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

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["author_id"] = request.user.id
        data["article_id"] = kwargs.get("article_id")
        data["parent_id"] = kwargs.get("parent_id")
        data["content"] = request.data.get("content")
        serializer = self.get_serializer(data=data)
        serializer.is_valid(True)

        instance = serializer.save()
        BBSReply.objects.create(comment=instance, is_article=False)
        parent = Comments.objects.filter(id=kwargs.get("parent_id")).first()
        article = Articles.objects.filter(id=kwargs.get("article_id")).first()
        parent.comment_num += 1
        article.comment_num += 1
        parent.save()
        article.save()
        return APIResponse(self.code["create"], "成功添加数据", serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return APIResponse(response_code.METHOD_NOT_ALLOWED, "无效的请求方式")


__all__ = [
    "ArticleView",
    "CommentView",
    "ChildrenCommentView",
]
