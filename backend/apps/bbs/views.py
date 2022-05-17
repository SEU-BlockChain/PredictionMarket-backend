from rest_framework.decorators import action
from .serializers import *
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
    filter_fields = ["author", "author__username", "category_id"]
    ordering_fields = ["update_time", "create_time", "view_num", "up_num", "comment_num"]
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
        if not Article.objects.filter(id=pk, is_active=True).exists():
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
        author_id = Article.objects.filter(id=pk).first().author.id
        if not author_id:
            return APIResponse(response_code.INVALID_PARAMS, "缺少参数")

        data = Article.objects.filter(
            is_active=True,
            author_id=author_id
        ).exclude(id=pk).order_by("-up_num")[:10].values("title", "id")

        return APIResponse(response_code.SUCCESS_GET_RECOMMEND, "成功获取推荐", data)


class CommentView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    queryset = Comment.objects.filter(is_active=True, parent_id=None, article__is_active=True)
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

        article = Article.objects.filter(id=article_id, is_active=True).first()
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
        if not Comment.objects.filter(article_id=article_id, article__is_active=True, id=pk, is_active=True).exists():
            return APIResponse(response_code.INEXISTENT_COMMENTS, "评论不存在")

        data = request.data.copy()
        data["user_id"] = request.user.id
        data["comment_id"] = pk
        ser = VoteCommentSerializer(data=data)
        ser.is_valid(True)
        ser.save()

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

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["author_id"] = request.user.id
        data["article_id"] = kwargs.get("article_id")
        data["parent_id"] = kwargs.get("parent_id")
        data["content"] = request.data.get("content")
        serializer = self.get_serializer(data=data)
        serializer.is_valid(True)

        parent = Comment.objects.filter(id=kwargs.get("parent_id")).first()
        article = Article.objects.filter(id=kwargs.get("article_id")).first()
        parent.comment_num += 1
        article.comment_num += 1
        parent.save()
        article.save()
        return APIResponse(self.code["create"], "成功添加数据", serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return APIResponse(response_code.METHOD_NOT_ALLOWED, "无效的请求方式")
