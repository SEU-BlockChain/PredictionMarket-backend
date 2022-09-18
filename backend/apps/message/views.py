from django.db.models import Q
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from .serializers import *
from backend.libs.wraps.authenticators import CommonJwtAuthentication
from backend.libs.wraps.views import APIModelViewSet
from backend.libs.wraps.response import APIResponse
from backend.libs.constants import response_code
from backend.libs.scripts.sql import like_sql, private_sql


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
        "bbs_comment__content",
        "special_column__title",
        "special_comment__content",
    ]

    def get_queryset(self):
        return self.request.user.dynamic_me.filter(
            is_active=True,
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
        return self.request.user.reply_me.filter(
            Q(is_active=True) & ~Q(sender_id__in=self.request.user.my_black_set)
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
        return self.request.user.at_me.filter(
            Q(is_active=True) & ~Q(sender_id__in=self.request.user.my_black_set)
        ).order_by("-id")

    def after_list(self, queryset, request, *args, **kwargs):
        request.user.at_me.all().filter(is_active=True, is_viewed=False).update(is_viewed=True)


class SystemView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    serializer_class = SystemSerializer
    queryset = System
    code = {
        "list": response_code.SUCCESS_GET_SYSTEM_LIST,
        "destroy": response_code.SUCCESS_DELETE_SYSTEM
    }
    exclude = ["create", "retrieve", "update"]

    def get_queryset(self):
        return self.request.user.system_me.filter(is_active=True).order_by("-id")

    def after_list(self, queryset, request, *args, **kwargs):
        request.user.system_me.all().filter(is_active=True, is_viewed=False).update(is_viewed=True)


class PrivateView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    serializer_class = PrivateSerializer
    queryset = Private
    code = {
        "list": response_code.SUCCESS_GET_PRIVATE_LIST,
        "destroy": response_code.SUCCESS_DELETE_PRIVATE
    }
    exclude = ["create", "retrieve", "update"]

    def get_queryset(self):
        return Private.objects.raw(private_sql.format(user_id=self.request.user.id))

    def destroy(self, request, *args, **kwargs):
        pass


class PrivateDetailView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    serializer_class = PrivateDetailSerializer
    queryset = Private
    code = {
        "list": response_code.SUCCESS_GET_PRIVATE_DETAIL_LIST,
        "create": response_code.SUCCESS_POST_PRIVATE_DETAIL,
        "destroy": response_code.SUCCESS_DELETE_PRIVATE_DETAIL
    }
    exclude = ["retrieve", "update"]

    def get_queryset(self):
        if self.action == "list":
            return Private.objects.filter(
                is_active=True,
            ).filter(
                Q(
                    sender_id=self.request.user.id,
                    receiver_id=self.request.query_params.get("uid"),
                ) | Q(
                    sender_id=self.request.query_params.get("uid"),
                    receiver_id=self.request.user.id
                )
            ).all().order_by("-time")

        return Private.objects.all()

    def after_list(self, queryset, request, *args, **kwargs):
        queryset = Private.objects.filter(
            Q(
                sender_id=self.request.user.id,
                receiver_id=self.request.query_params.get("uid"),
                is_viewed=False
            ) | Q(
                sender_id=self.request.query_params.get("uid"),
                receiver_id=self.request.user.id,
                is_viewed=False
            )
        )
        for i in queryset:
            i.is_viewed = True
        Private.objects.bulk_update(queryset, ["is_viewed"])
