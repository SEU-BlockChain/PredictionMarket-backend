from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from .serializers import *
from backend.libs.wraps.authenticators import CommonJwtAuthentication
from backend.libs.wraps.views import APIModelViewSet
from backend.libs.wraps.response import APIResponse
from backend.libs.constants import response_code
from backend.libs.scripts.sql import like_sql


class MessageSettingView(ViewSet):
    authentication_classes = [CommonJwtAuthentication]

    @action(["GET", "POST"], False)
    def message_setting(self, request):
        if request.method == "GET":
            return APIResponse(
                response_code.SUCCESS_GET_MESSAGE_SETTING,
                "成功获取消息设置",
                MessageSettingSerializer(self.request.user.message_setting).data)
        else:
            print(request.data)
            ser = MessageSettingSerializer(request.user.message_setting, request.data)
            ser.is_valid(True)
            ser.save()
            return APIResponse(response_code.SUCCESS_EDIT_MESSAGE_SETTING)


class DynamicView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    serializer_class = DynamicSerializer
    queryset = Dynamic
    code = {
        "list": response_code.SUCCESS_GET_DYNAMIC_LIST,
        "destroy": response_code.SUCCESS_DELETE_DYNAMIC
    }
    exclude = ["create", "retrieve", "update", "retrieve"]
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


class LikeView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    serializer_class = LikeSerializer
    code = {
        "list": response_code.SUCCESS_GET_LIKE_LIST,
    }
    exclude = ["create", "retrieve", "update", "destroy"]

    def get_queryset(self):
        return Like.objects.raw(like_sql % self.request.user.id)

    def after_list(self, queryset, request, *args, **kwargs):
        request.user.like_me.all().filter(is_active=True, is_viewed=False).update(is_viewed=True)


class AtView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    serializer_class = AtSerializer
    queryset = At
    code = {
        "list": response_code.SUCCESS_GET_AT_LIST,
        "destroy": response_code.SUCCESS_DELETE_AT
    }
    exclude = ["create", "retrieve", "update"]

    def get_queryset(self):
        return self.queryset.objects.filter(
            is_active=True,
            receiver=self.request.user,
            sender_id__in=self.request.user.my_follow_set - self.request.user.my_black_set
        ).order_by("-id")

    def after_list(self, queryset, request, *args, **kwargs):
        request.user.at_me.all().filter(is_active=True, is_viewed=False).update(is_viewed=True)
