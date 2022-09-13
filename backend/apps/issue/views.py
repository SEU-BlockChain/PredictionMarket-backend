from rest_framework.decorators import action
from django.db.models import Q

from .serializers import *
from message.models import Dynamic, MessageSetting, Like, Reply, Origin, At
from backend.libs.constants import response_code
from backend.libs.wraps.views import APIModelViewSet
from backend.libs.wraps.response import APIResponse
from backend.libs.wraps.authenticators import CommonJwtAuthentication, UserInfoAuthentication


class IssueCommentView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    queryset = IssueComment.objects.filter(is_active=True, parent_id=None)
    serializer_class = IssueCommentSerializer
    exclude = ["update", "retrieve"]
    ordering_fields = ["comment_time", "up_num", "comment_num"]
    code = {
        "create": response_code.SUCCESS_POST_COMMENT,
        "list": response_code.SUCCESS_GET_COMMENT_LIST,
        "destroy": response_code.SUCCESS_DELETE_COMMENT,
    }

    def get_authenticators(self):
        if self.request.method == "GET":
            return [UserInfoAuthentication()]

        return super().get_authenticators()

    def get_queryset(self):
        queryset = self.queryset.filter(issue__address=self.kwargs.get("address"))
        if self.action in ["vote", "list"]:
            return queryset

        return queryset.filter(author=self.request.user)

    def after_destroy(self, instance: IssueComment, request, *args, **kwargs):
        Dynamic.handle_delete(instance, Origin.ISSUE_COMMENT)
        Like.handle_delete(instance, Origin.ISSUE_COMMENT)
        Reply.handle_delete(instance, Origin.ISSUE_COMMENT)
        At.handle_delete(instance, Origin.ISSUE_COMMENT)

    @action(["POST"], True)
    def vote(self, request, address, pk):
        comment = IssueComment.objects.filter(issue__address=address, id=pk, is_active=True)
        if not comment:
            return APIResponse(response_code.INEXISTENT_COMMENTS, "评论不存在")
        comment = comment.first()

        data = request.data.copy()
        data["user_id"] = request.user.id
        data["comment_id"] = pk
        ser = VoteCommentSerializer(data=data)
        ser.is_valid(True)
        ser.save()

        receiver = comment.author
        sender = request.user
        if receiver != sender and receiver.message_setting.like:
            like = Like.objects.filter(origin=Origin.ISSUE_COMMENT, bbs_comment=comment, sender=sender)
            if request.data.get("is_up") and not like:
                Like.objects.create(
                    origin=Origin.ISSUE_COMMENT,
                    bbs_comment_id=pk,
                    sender=sender,
                    receiver=receiver,
                    is_viewed=receiver.is_viewed(sender, "like")
                )
            else:
                like = like.first()
                like.time = datetime.now()
                like.is_active = request.data.get("is_up") and not like.is_active
                like.save()

        return APIResponse(response_code.SUCCESS_VOTE_COMMENT, "评价成功")


class IssueChildrenCommentView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    queryset = IssueComment.objects.filter(is_active=True, parent_id__isnull=False, parent__is_active=True)
    serializer_class = ChildrenCommentSerializer
    code = {
        "create": response_code.SUCCESS_POST_COMMENT,
        "retrieve": response_code.SUCCESS_GET_COMMENT,
        "list": response_code.SUCCESS_GET_COMMENT_LIST,
        "destroy": response_code.SUCCESS_DELETE_COMMENT,
    }

    def get_authenticators(self):
        if self.request.method == "GET":
            return [UserInfoAuthentication()]

        return super().get_authenticators()

    def get_queryset(self):
        order = self.request.query_params.get("order", "id")
        return self.queryset.filter(parent_id=self.kwargs.get("parent_id")).order_by(order).all()

    def before_create(self, request, *args, **kwargs):
        request.data["address"] = kwargs.pop("address", None)
        request.data["parent_id"] = kwargs.pop("parent_id", None)

    def after_create(self, instance: IssueComment, request, *args, **kwargs):
        instance.parent.comment_num += 1
        instance.parent.save()

        receiver = instance.target.author if instance.target else instance.parent.author
        sender = request.user

        if receiver != sender and receiver.message_setting.reply:
            Reply.objects.create(
                origin=Origin.ISSUE_COMMENT,
                bbs_comment=instance,
                sender=sender,
                receiver=receiver,
                is_viewed=receiver.is_viewed(sender, "reply")
            )

    def after_destroy(self, instance: IssueComment, request, *args, **kwargs):
        instance.parent.comment_num -= 1
        instance.parent.save()

        Dynamic.handle_delete(instance, Origin.ISSUE_COMMENT)
        Like.handle_delete(instance, Origin.ISSUE_COMMENT)
        Reply.handle_delete(instance, Origin.ISSUE_COMMENT)
        At.handle_delete(instance, Origin.ISSUE_COMMENT)
