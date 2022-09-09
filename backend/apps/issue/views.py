from rest_framework.decorators import action
from django.db.models import Q

from .serializers import *
from message.models import Dynamic, MessageSetting, Like, Reply, Origin, At
from backend.libs.constants import response_code
from backend.libs.wraps.views import APIModelViewSet
from backend.libs.wraps.response import APIResponse
from backend.libs.wraps.authenticators import CommonJwtAuthentication, UserInfoAuthentication

# class IssueCommentView(APIModelViewSet):
#     authentication_classes = [CommonJwtAuthentication]
#     queryset = IssueComment.objects.filter(is_active=True, author__is_active=True)
#     serializer_class = IssueCommentSerializer
#     exclude = ["update", "retrieve"]
#     code = {
#         "create": response_code.SUCCESS_POST_COMMENT,
#         "list": response_code.SUCCESS_GET_COMMENT_LIST,
#         "destroy": response_code.SUCCESS_DELETE_COMMENT,
#     }
#
#     def get_authenticators(self):
#         if self.request.method == "GET":
#             return [UserInfoAuthentication()]
#
#         return super().get_authenticators()
#
#     def get_queryset(self):
#         queryset = self.queryset.filter(issue=self.kwargs.get("address"))
#         if self.action in ["vote", "list"]:
#             return queryset
#
#         return queryset.filter(author=self.request.user)
#
#     @action(["POST"], True)
#     def vote(self, request, address, pk):
#         comment = IssueComment.objects.filter(issue__address=address, article__is_active=True, id=pk, is_active=True)
#         if not comment:
#             return APIResponse(response_code.INEXISTENT_COMMENTS, "评论不存在")
#         comment = comment.first()
#
#         data = request.data.copy()
#         data["user_id"] = request.user.id
#         data["comment_id"] = pk
#         ser = VoteCommentSerializer(data=data)
#         ser.is_valid(True)
#         ser.save()
#
#         receiver = comment.author
#         sender = request.user
#         if receiver != sender and receiver.message_setting.like:
#             like = Like.objects.filter(origin=Origin.BBS_COMMENT, bbs_comment=comment, sender=sender)
#             if request.data.get("is_up") and not like:
#                 Like.objects.create(
#                     origin=Origin.BBS_COMMENT,
#                     bbs_comment_id=pk,
#                     sender=sender,
#                     receiver=receiver,
#                     is_viewed=receiver.is_viewed(sender, "like")
#                 )
#             else:
#                 like = like.first()
#                 like.time = datetime.datetime.now()
#                 like.is_active = request.data.get("is_up") and not like.is_active
#                 like.save()
#
#         return APIResponse(response_code.SUCCESS_VOTE_COMMENT, "评价成功")
# class IssueChildrenCommentView(APIModelViewSet):
#     pass
