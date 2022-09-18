from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from backend.libs.wraps.response import APIResponse


class InfoView(ViewSet):
    @action(["GET"], False)
    def version(self, request):
        return APIResponse(result={"version": [0, 1, 0, 3]})
