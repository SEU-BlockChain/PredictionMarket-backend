import datetime

from django.core.files.base import File
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from .serializers import *
from backend.libs.wraps.response import UserInfoResponse, APIResponse
from backend.libs.wraps.authenticators import CommonJwtAuthentication, UserInfoAuthentication
from backend.libs.wraps.views import APIModelViewSet
from backend.libs.constants import response_code


class VoteView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    serializer_class = VoteSerializer
    queryset = Vote.objects.filter(is_active=True).all().order_by("-create_time")
    exclude = ["update"]
    code = {
        "create": response_code.SUCCESS_CREATE_VOTE,
        "retrieve": response_code.SUCCESS_GET_VOTE,
        "list": response_code.SUCCESS_GET_VOTE_LIST,
        "destroy": response_code.SUCCESS_DELETE_VOTE,
    }

    def get_authenticators(self):
        if self.request.method == "GET":
            return [UserInfoAuthentication()]

        return super().get_authenticators()

    def get_queryset(self):
        if self.action == "destroy":
            return self.queryset.filter(creator=self.request.user)

        return self.queryset

    @action(["POST"], True)
    def submit(self, request, pk):
        selected = request.data.get("selected")

        vote = Vote.objects.filter(id=pk).first()

        if not vote:
            return APIResponse(response_code.NOT_FOUND, "投票不存在")

        if not vote.start_time < datetime.datetime.now() < vote.end_time:
            return APIResponse(response_code.VOTE_NOT_OPENED, "投票不在开放时间")

        if not (vote.min_num <= len(selected) <= vote.max_num):
            return APIResponse(response_code.INVALID_SELECTED_NUM, "选项数目错误")

        if VoteToUser.objects.filter(user=request.user, vote=vote).exists():
            return APIResponse(response_code.HAS_VOTED, "您已经投过票了")

        VoteToUser.objects.create(user=request.user, vote=vote)
        ChoiceToUser.objects.bulk_create(map(lambda x: ChoiceToUser(user=request.user, choice_id=x), selected))

        return APIResponse(response_code.SUCCESS_VOTE, "已投票")
