from .models import *
from backend.libs.wraps.serializers import APIModelSerializer


class InfoSerializer(APIModelSerializer):
    class Meta:
        model = Daily
        fields = [
            "sign",
            "bbs_post",
            "column_post",
            "answer_adopted",
            "comment",
            "like",
            "comment_liked",
            "post_liked",
            "commented",
            "stared",
        ]
