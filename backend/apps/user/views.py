import datetime

from django.core.files.base import File
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from .serializers import *
from message.models import Dynamic
from backend.libs.wraps.response import UserInfoResponse, OtherUserInfoResponse, APIResponse
from backend.libs.wraps.authenticators import CommonJwtAuthentication, UserInfoAuthentication
from backend.libs.wraps.views import APIModelViewSet, Pag
from backend.utils.COS import *
from bbs.models import Comment
from bbs.serializers import SelfCommentSerializer


class SignView(ViewSet):
    @action(["POST"], False)
    def register(self, request):
        method = request.data.get("method")

        if method:
            ser = PhoneRegisterSerializer(data=request.data)
        else:
            ser = UsernameRegisterSerializer(data=request.data)

        ser.is_valid(True)
        user = ser.save()

        return UserInfoResponse(user, response_code.SUCCESS_REGISTER, "注册成功")

    @action(["POST"], False)
    def login(self, request):
        ser = LoginSerializer(data=request.data)

        ser.is_valid(True)
        user = ser.context["user"]
        user.last_login = datetime.datetime.now()
        user.save()

        return UserInfoResponse(user, response_code.SUCCESS_LOGIN, "登录成功")


class UserInfoView(ViewSet):
    def get_authenticators(self):
        if self.request.META.get("PATH_INFO") == "/user/reset_password/":
            return None
        return [CommonJwtAuthentication()]

    @action(["GET", "POST"], False)
    def info(self, request):
        if request.method == "GET":
            return UserInfoResponse(request.user, response_code.SUCCESS_GET_USER_INFO, "成功获取用户信息")
        else:
            ser = UserInfoSerializer(request.user, request.data)

            ser.is_valid(True)

            user = ser.save()
            return UserInfoResponse(user, response_code.SUCCESS_POST_USER_INFO, "成功修改用户信息")

    @action(["POST"], False)
    def reset_password(self, request):
        ser = ResetPasswordSerializer(User.objects, request.data)

        ser.is_valid(True)

        ser.save()
        return APIResponse(response_code.SUCCESS_RESET_PASSWORD, "重置密码成功")

    @action(["POST"], False)
    def change_password(self, request):
        ser = ChangePasswordSerializer(request.user, request.data)
        ser.is_valid(True)

        if not request.user.check_password(ser.validated_data.get("old_password")):
            return APIResponse(response_code.INCORRECT_PASSWORD, "原密码错误")

        ser.save()
        return APIResponse(response_code.SUCCESS_RESET_PASSWORD, "重置密码成功")

    @action(["POST"], False)
    def bind_phone(self, request):
        ser = BindPhoneView(request.user, request.data)

        ser.is_valid(True)

        ser.save()
        return APIResponse(response_code.SUCCESS_BIND_PHONE, "绑定手机成功")

    @action(["POST"], False)
    def unbind_phone(self, request):
        ser = UnbindPhoneView(request.user, request.data)

        ser.is_valid(True)

        ser.save()
        return APIResponse(response_code.SUCCESS_UNBIND_PHONE, "解除绑定成功")

    @action(["POST"], False)
    def icon(self, request):
        file = request.data.get("icon")
        user = request.user
        if not isinstance(file, File):
            return APIResponse(response_code.WRONG_FORM, "请上传图片")

        form = str(file).split(".")[-1]
        if form.lower() not in ("jpg", "png", "bmp", "jpeg"):
            return APIResponse(response_code.WRONG_FORM, "不支持的图片格式")

        if file.size / (1024 * 1024) > 5:
            return APIResponse(response_code.EXCEEDED_SIZE, "图片不能超过5M")

        if user.icon != "icon/default.jpg":
            delete_obj(user.icon)

        path = f"icon/{user.id}.{form}"
        if user.icon != path:
            user.icon = path
            user.save()
        put_obj(file, path)
        return APIResponse(response_code.SUCCESS_CHANGE_ICON, "修改头像成功")

    @action(["GET"], False)
    def comment(self, request):
        instance = Comment.objects.filter(
            article__is_active=True,
            author=request.user,
            is_active=True
        ).order_by(
            "-comment_time"
        )
        pag = Pag()
        paged_instance = pag.paginate_queryset(instance, request, view=self)
        ser = SelfCommentSerializer(paged_instance, many=True, context={"view": self, "request": request})
        return pag.get_paginated_response([response_code.SUCCESS_GET_COMMENT_LIST, ser.data])

    @action(["GET"], False)
    def message(self, request):
        data = {
            "dynamic": request.user.dynamic_me.all().filter(is_active=True, is_viewed=False).count(),
            "at": request.user.at_me.all().filter(is_active=True, is_viewed=False).count(),
            "private": request.user.private_me.all().filter(is_active=True, is_viewed=False).count(),
            "system": request.user.system_me.all().filter(is_active=True, is_viewed=False).count(),
            "like": request.user.like_me.all().filter(is_active=True, is_viewed=False).count(),
            "reply": request.user.reply_me.all().filter(is_active=True, is_viewed=False).count(),
        }
        return APIResponse(response_code.SUCCESS_GET_MESSAGE_SUM, "成功获取消息", data)


class OtherUserView(APIModelViewSet):
    authentication_classes = [UserInfoAuthentication]
    queryset = User.objects.all().order_by("id")
    serializer_class = OtherUserSerializer
    code = {
        "retrieve": response_code.SUCCESS_GET_OTHER_USER_INFO,
        "list": response_code.SUCCESS_GET_OTHER_USER_INFO_LIST
    }
    exclude = ["destroy", "update", "create"]
    search_fields = [
        "id",
        "username",
    ]


class FollowView(ViewSet):
    authentication_classes = [CommonJwtAuthentication]

    def get_authenticators(self):
        if self.request.method == "GET":
            return [UserInfoAuthentication()]

        return super().get_authenticators()

    @action(["GET"], True)
    def as_follower(self, request, pk, *args, **kwargs):
        name = request.query_params.get("name", "")
        instance = User.objects.get(id=pk).my_follow.all().filter(
            followed__username__icontains=name,
        ).exclude(
            followed__in=request.user.my_black_set
        ).order_by(
            "-create_time"
        )
        pag = Pag()
        paged_instance = pag.paginate_queryset(instance, request, view=self)
        ser = FollowSerializer(paged_instance, many=True, context={"view": self, "request": request})
        return pag.get_paginated_response([response_code.SUCCESS_GET_FOLLOWED, ser.data])

    @action(["GET"], True)
    def as_followed(self, request, pk, *args, **kwargs):
        name = request.query_params.get("name", "")
        instance = User.objects.get(id=pk).follow_me.all().filter(
            follower__username__icontains=name,
        ).exclude(
            follower__in=request.user.my_black_set
        ).order_by(
            "-create_time"
        )
        pag = Pag()
        paged_instance = pag.paginate_queryset(instance, request, view=self)
        ser = FollowSerializer(paged_instance, many=True, context={"view": self, "request": request})
        return pag.get_paginated_response([response_code.SUCCESS_GET_FOLLOWER, ser.data])

    @action(["POST"], True)
    def add(self, request, pk, *args, **kwargs):
        if request.user.id == int(pk):
            return APIResponse(response_code.NOT_SELF, "不能关注自己")
        if request.user.my_follow.filter(followed=pk).exists():
            return APIResponse(response_code.FOLLOWED, "你已经关注过他了")

        user = User.objects.filter(id=pk)
        if not user:
            return APIResponse(response_code.INVALID_PK, "用户不存在")

        Follow.add(request.user, user.first())
        return APIResponse(response_code.SUCCESS_FOLLOW, "已关注")

    @action(["POST"], True)
    def remove(self, request, pk, *args, **kwargs):
        if not request.user.my_follow.filter(followed=pk).exists():
            return APIResponse(response_code.NOT_FOLLOWED, "未关注")

        user = User.objects.filter(id=pk)
        if not user:
            return APIResponse(response_code.INVALID_PK, "用户不存在")

        Follow.remove(request.user, user.first())
        return APIResponse(response_code.SUCCESS_NOT_FOLLOW, "已取消关注")


class BlackListView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    exclude = ["retrieve", "update"]

    def list(self, request, *args, **kwargs):
        name = request.query_params.get("name", "")
        instance = request.user.my_black.all().filter(blacked__username__icontains=name).order_by("-create_time")
        pag = Pag()
        paged_instance = pag.paginate_queryset(instance, request, view=self)
        ser = BlackListSerializer(paged_instance, many=True, context={"view": self, "request": request})
        return pag.get_paginated_response([response_code.SUCCESS_GET_BLACKED, ser.data])

    def create(self, request, *args, **kwargs):
        pk = request.data.get("id", None)
        user = User.objects.filter(id=pk)
        if not user:
            return APIResponse(response_code.INVALID_PK, "用户不存在")

        if request.user.id == int(pk):
            return APIResponse(response_code.NOT_SELF, "不能拉黑自己")

        if request.user.my_black.filter(blacked=pk).exists():
            return APIResponse(response_code.BLACKED, "你已经拉黑过他了")

        BlackList.add(request.user, user.first())
        return APIResponse(response_code.SUCCESS_BLACKED, "已拉黑")

    def destroy(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        user = User.objects.filter(id=pk)
        if not user:
            return APIResponse(response_code.INVALID_PK, "用户不存在")

        if not request.user.my_black.filter(blacked=pk).exists():
            return APIResponse(response_code.NOT_BLACKED, "未拉黑")

        BlackList.remove(request.user, user.first())
        return APIResponse(response_code.SUCCESS_NOT_BLACKED, "已取消拉黑")
