from .serializers import *
from backend.libs.wraps.authenticators import CommonJwtAuthentication
from backend.libs.wraps.views import APIModelViewSet
from backend.libs.constants import response_code


class DynamicView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    serializer_class = DynamicSerializer
    queryset = Dynamic
    code = {
        "list": response_code.SUCCESS_GET_DYNAMIC_LIST,
        "destroy": response_code.SUCCESS_DELETE_DYNAMIC
    }
    exclude = ["create", "retrieve", "update"]
    search_fields = [
        "sender__id",
        "sender__username",
        "bbs_article__title",
    ]

    def get_queryset(self):
        return self.queryset.objects.filter(
            is_active=True,
            receiver=self.request.user,
            sender_id__in=self.request.user.my_follow_set - self.request.user.my_black_set
        ).order_by("-id")

    def after_list(self, queryset, request, *args, **kwargs):
        request.user.dynamic_me.all().filter(is_active=True, is_viewed=False).update(is_viewed=True)


class ReplyView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    serializer_class = ReplySerializer
    queryset = Reply
    code = {
        "list": response_code.SUCCESS_GET_REPLY_LIST,
        "destroy": response_code.SUCCESS_DELETE_REPLY
    }
    exclude = ["create", "retrieve", "update"]

    def get_queryset(self):
        return self.queryset.objects.filter(
            is_active=True,
            receiver=self.request.user,
            sender_id__in=self.request.user.my_follow_set - self.request.user.my_black_set
        ).order_by("-id")

    def after_list(self, queryset, request, *args, **kwargs):
        request.user.reply_me.all().filter(is_active=True, is_viewed=False).update(is_viewed=True)
