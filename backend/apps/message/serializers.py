from .models import *
from backend.libs import *

# from bbs.serializers import B
#
# class ReplySerializer(serializers.ModelSerializer):
#     comment = serializers.SerializerMethodField()
#
#     def get_comment(self, instance: Reply):
#         if instance.reply_type == 0:
#             return BBSRootCommentSerializer(instance.bbs_comment).data
#         if instance.reply_type == 1:
#             return BBSChildrenCommentSerializer(instance.bbs_comment).data
#
#     class Meta:
#         model = Reply
#         fields = [
#             "id",
#             "reply_type",
#             "reply_time",
#             "is_viewed",
#             "comment"
#         ]
