from rest_framework_jwt.serializers import jwt_payload_handler, jwt_encode_handler
from django.db.models import QuerySet, F
from user.models import User
from ..wraps.serializers import UserSerializer,OtherUserSerializer

def getToken(user):
    if isinstance(user, QuerySet):
        user = user.first()
    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)
    return token


def getUserInfo(user: User):
    info = {
        "id": user.id,
        "username": user.username,
        "date_joined": user.date_joined,
        "phone": user.phone,
        "icon": user.icon,
        "description": user.description,
        "experience": user.experience,
        "metal": user.metal.filter(
            is_active=True,
            usertometal__is_active=True
        ).annotate(
            obtain_time=F("usertometal__obtain_time")
        ).values("id", "description", "obtain_time").all(),
        "is_staff": user.is_superuser,
        "up_num": user.up_num,
        "attention_num": user.attention_num,
        "fans_num": user.fans_num,
    }
    permission = user.permission.filter(
        is_active=True,
        usertopermission__is_active=True
    ).annotate(
        permission_id=F("id")
    ).values(
        "permission_id"
    ).all()

    group = user.group.filter(
        is_active=True,
        grouptopermission__is_active=True,
        grouptopermission__permission_id__is_active=True
    ).annotate(
        permission_id=F("grouptopermission__permission_id")
    ).values(
        "permission_id"
    ).all()

    info["permissions"] = list(permission) + list(group)

    return info


def getOtherUserInfo(self: User, user: User):
    info = {
        "id": user.id,
        "username": user.username,
        "date_joined": user.date_joined,
        "phone": user.phone,
        "icon": user.icon,
        "description": user.description,
        "experience": user.experience,
        "metal": user.metal.filter(
            is_active=True,
            usertometal__is_active=True
        ).annotate(
            obtain_time=F("usertometal__obtain_time")
        ).values("id", "description", "obtain_time").all(),
        "up_num": user.up_num,
        "attention_num": user.attention_num,
        "fans_num": user.fans_num,
    }
    if not self.is_anonymous:
        info["followed"] = self.my_follow.filter(followed=user).exists()
    return info


__all__ = [
    "getToken",
    "getUserInfo",
    "getOtherUserInfo",
]
