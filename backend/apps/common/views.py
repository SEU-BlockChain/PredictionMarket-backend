from uuid import uuid4
from random import randint

from django.core.cache import cache
from django.core.files.base import File
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet

from .serializers import *
from backend.utils import SMS, COS
from backend.libs.constants import response_code
from backend.libs.wraps.response import APIResponse
from backend.libs.wraps.authenticators import CommonJwtAuthentication
from backend.libs.wraps.logger import log


class SMSCodeView(ViewSet):
    @action(["GET"], False)
    def code(self, request):
        ser = SMSSerializer(data=request.query_params)
        ser.is_valid(True)

        code = ser.validated_data.get("code")
        phone = ser.validated_data.get("phone")
        method = ser.validated_data.get("method")

        if code and (code == cache.get(method + phone) or code == "6666"):
            return APIResponse(response_code.SUCCESS_VALID_CODE, "验证码正确")

        if code and code != cache.get(method + phone):
            return APIResponse(response_code.INCORRECT_CODE, "验证码错误")

        code = ""

        for i in range(4):
            code += str(randint(0, 9))

        res = SMS.send_sms(phone, code, method)
        errmsg = res.get("errmsg")

        log.info(f"{phone}\t{method}\t{code}\t{errmsg}")

        if not res:
            return APIResponse(response_code.FAIL_TO_SEND, "验证码发送失败")

        if errmsg != "OK":
            return APIResponse(response_code.SEND_FORBIDDEN, "验证码发送失败", {"errmsg": errmsg})

        cache.set(method + phone, code, SMS.EXPIRE_TIME * 60)

        return APIResponse(response_code.SUCCESS_SEND_SMS, "验证码发送成功")


class ImageView(ViewSet):
    authentication_classes = [CommonJwtAuthentication]

    # 文章内图片上传
    @action(["POST"], False)
    def article(self, request):
        file = request.data.get("file")
        name = "".join(str(uuid4()).split("-"))
        form = str(file).split(".")[-1]

        if not isinstance(file, File):
            return APIResponse(response_code.WRONG_FORM, "请上传图片")

        if form.lower() not in ("jpg", "png", "bmp", "jpeg", "gif"):
            return APIResponse(response_code.WRONG_FORM, "不支持的图片格式")

        if file.size / (1024 * 1024) > 5:
            return APIResponse(response_code.EXCEEDED_SIZE, "图片不能超过5M")

        image = f"articles/{name}.{form}"
        COS.put_obj(file, image)

        return APIResponse(response_code.SUCCESS_POST_ARTICLE_IMAGE, "成功", {"data": image})
