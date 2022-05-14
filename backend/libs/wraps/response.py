from rest_framework.response import Response
from backend.libs import getUserInfo, getOtherUserInfo, getToken, response_code


class APIResponse(Response):
    def __init__(self, code=None, msg=None, result=None, status=None, headers=None, content_type=None, **kwargs):
        """
        :param code: 自定义响应代码
        :param msg: 响应摘要
        :param result: 响应数据
        :param status: HTTPS响应代码
        :param headers: 额外响应头
        :param content_type:响应编码
        :param kwargs: 额外响应内容
        """
        dic = {"code": code or 100, "msg": msg or "成功", "result": result or {}}
        dic.update(kwargs)
        super().__init__(data=dic, status=status, headers=headers, content_type=content_type)


def InvalidParamsResponse():
    return APIResponse(response_code.INVALID_PARAMS, "缺少参数")


def UserInfoResponse(user, code, msg=None, token=False):
    user_info = getUserInfo(user)
    if token:
        return APIResponse(code, msg, {"user": user_info, "token": getToken(user)})

    return APIResponse(code, msg, {"user": user_info})


def OtherUserInfoResponse(self, user, code, msg=None):
    user_info = getOtherUserInfo(self, user)
    return APIResponse(code, msg, {"user": user_info})


__all__ = [
    "APIResponse",
    "UserInfoResponse",
    "OtherUserInfoResponse",
    "InvalidParamsResponse",
]
