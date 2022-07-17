from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from .serializers import *
from backend.libs.constants import response_code
from backend.libs.wraps.response import APIResponse
from backend.libs.wraps.authenticators import CommonJwtAuthentication


class InfoView(ViewSet):
    authentication_classes = [CommonJwtAuthentication]

    @action(["GET"], False)
    def info(self, request):
        record = request.user.daily
        return APIResponse(response_code.SUCCESS_GET_TASK_INFO, "获取成功", result=InfoSerializer(record).data)
