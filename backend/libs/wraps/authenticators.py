import jwt

from rest_framework_jwt.authentication import BaseJSONWebTokenAuthentication
from rest_framework_jwt.authentication import jwt_decode_handler
from rest_framework.exceptions import AuthenticationFailed

list
class CommonJwtAuthentication(BaseJSONWebTokenAuthentication):
    def authenticate(self, request):
        token = request.META.get("HTTP_AUTHORIZATION")
        if token:
            try:
                payload = jwt_decode_handler(token)
            except jwt.ExpiredSignature:
                raise AuthenticationFailed("登录信息过期，请重新登陆")
            except jwt.InvalidTokenError:
                raise AuthenticationFailed("登录信息变动，请重新登陆")
            except Exception as e:
                raise AuthenticationFailed(str(e))

            user = self.authenticate_credentials(payload)
            return user, token

        raise AuthenticationFailed("缺少签名")


class UserInfoAuthentication(BaseJSONWebTokenAuthentication):
    def authenticate(self, request):
        token = request.META.get("HTTP_AUTHORIZATION")
        if token:
            try:
                payload = jwt_decode_handler(token)
                user = self.authenticate_credentials(payload)
                return user, token
            except Exception:
                pass
        return None


class StaffJwtAuthentication(CommonJwtAuthentication):
    def authenticate(self, request):
        user, token = super().authenticate(request)
        if not user.is_staff:
            raise AuthenticationFailed("不是管理员账号")

        return user, token


__all__ = [
    "CommonJwtAuthentication",
    "UserInfoAuthentication",
    "StaffJwtAuthentication"
]
