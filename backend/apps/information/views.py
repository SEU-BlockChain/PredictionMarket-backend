from .serializers import *
from backend.libs.constants import response_code
from backend.libs.wraps.views import APIModelViewSet
from backend.libs.wraps.authenticators import PermissionAuthentication, UserInfoAuthentication


class NewsView(APIModelViewSet):
    queryset = News.objects.all()
    authentication_classes = [PermissionAuthentication("news_author")]
    serializer_class = NewsSerializer
    code = {
        "create": response_code.SUCCESS_POST_NEWS,
        "retrieve": response_code.SUCCESS_GET_NEWS,
        "update": response_code.SUCCESS_EDIT_NEWS,
        "list": response_code.SUCCESS_GET_NEWS_LIST,
        "destroy": response_code.SUCCESS_DELETE_NEWS,
    }

    def get_authenticators(self):
        if self.request.method == "GET":
            return [UserInfoAuthentication()]

        return super().get_authenticators()

    def get_queryset(self):
        if self.action in ["update", "destroy"] or self.request.query_params.get(
                "self") or self.request.query_params.get("raw"):
            return self.queryset.filter(is_active=True, author=self.request.user).order_by("-create_time")

        return self.queryset.filter(is_active=True, is_draft=False).order_by("-create_time")
