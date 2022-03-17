from rest_framework.views import exception_handler
from rest_framework import exceptions
from django.http import response
from .logger import log
from .response import APIResponse
from .errors import *
from backend.libs.constants import response_code


def common_exception_handler(exc, context):
    log.error("%s : %s" % (context["view"].__class__.__name__, str(exc)))

    print("Catch:\t", type(exc))

    if isinstance(exc, SerializerError):
        return APIResponse(exc.code, exc.msg)

    ret = exception_handler(exc, context)
    if not ret:
        return APIResponse(-1, "未知错误")
    else:
        if isinstance(exc, exceptions.ValidationError):
            return APIResponse(response_code.INVALID_PARAMS, "参数错误", ret.data)

        if isinstance(exc, exceptions.Throttled):
            return APIResponse(response_code.REQUEST_THROTTLED, "访问频率过快", ret.data)

        if isinstance(exc, exceptions.MethodNotAllowed):
            return APIResponse(response_code.METHOD_NOT_ALLOWED, "无效的请求方式", ret.data)

        if isinstance(exc, response.Http404):
            return APIResponse(response_code.NOT_FOUND, "资源未找到", ret.data)

        if isinstance(exc, exceptions.AuthenticationFailed):
            return APIResponse(response_code.NOT_LOGIN, "未登录", ret.data)

        return APIResponse(0, "错误", ret.data)


__all__ = [
    "common_exception_handler",
]
