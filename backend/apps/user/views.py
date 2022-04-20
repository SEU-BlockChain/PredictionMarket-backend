from django.core.files.base import File
from django.db.models import F, Q
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from .models import *
from .serializers import *
from backend.libs import *
from backend.utils.COS import *


class RegisterView(ViewSet):
    @action(["POST"], False)
    def register(self, request):
        method = request.data.get("method")

        if method:
            ser = PhoneRegisterSerializer(data=request.data)
        else:
            ser = UsernameRegisterSerializer(data=request.data)

        ser.is_valid(True)

        user = ser.save()

        return UserInfoResponse(user, response_code.SUCCESS_REGISTER, "注册成功", True)


class LoginView(ViewSet):
    @action(["POST"], False)
    def login(self, request):
        ser = LoginSerializer(data=request.data)

        ser.is_valid(True)

        user = ser.context["user"]

        return UserInfoResponse(user, response_code.SUCCESS_LOGIN, "登录成功", True)


class UserInfoView(ViewSet):
    def get_authenticators(self):
        if self.request.META.get("PATH_INFO") == "/user/reset_password/":
            return None
        return [CommonJwtAuthentication()]

    @action(["GET", "POST"], False)
    def user_info(self, request):
        if request.method == "GET":
            return UserInfoResponse(request.user, response_code.SUCCESS_GET_USER_INFO, "成功获取用户信息")
        else:
            ser = UserInfoSerializer(request.user, request.data)

            ser.is_valid(True)

            user = ser.save()
            return UserInfoResponse(user, response_code.SUCCESS_POST_USER_INFO, "成功修改用户信息", True)

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


class ReplyView(ViewSet):
    authentication_classes = [CommonJwtAuthentication]

    def list(self, request):
        instance = Reply.objects.filter(
            is_ignore=False,
        ).filter(
            Q(
                ~Q(bbs_comment__author=request.user) & Q(
                    reply_type=0,
                    bbs_comment__is_active=True,
                    bbs_comment__article__is_active=True,
                    bbs_comment__article__author=request.user,
                )
            ) | Q(
                ~Q(bbs_comment__author=request.user) & Q(
                    reply_type=1,
                    bbs_comment__is_active=True,
                    bbs_comment__article__is_active=True,
                    bbs_comment__target__is_active=True,
                    bbs_comment__parent__is_active=True,
                    bbs_comment__target__author=request.user
                )
            )
        ).order_by(
            "is_viewed",
            "-reply_time",
        ).all()

        pag = Pag()
        page_list = pag.paginate_queryset(instance, request, view=self)
        ser = ReplySerializer(page_list, many=True)
        return pag.get_paginated_response([response_code.SUCCESS_GET_REPLY_LIST, ser.data])


__all__ = [
    "RegisterView",
    "LoginView",
    "UserInfoView",
    "ReplyView",
]
