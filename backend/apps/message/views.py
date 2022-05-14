from django.core.files.base import File
from django.db.models import F, Q
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from .models import *
from .serializers import *
from backend.libs import *
from backend.utils.COS import *


# Create your views here.
class ReplyView(ViewSet):
    authentication_classes = [CommonJwtAuthentication]

    def list(self, request):
        instance = Reply.objects.filter(
            is_ignore=False,
        ).filter(
            Q(
                ~Q(bbs_comment__author=request.user) & Q(
                    reply_type=0,
                    bbs_comment__is_active=True,
                    bbs_comment__article__is_active=True,
                    bbs_comment__article__author=request.user,
                )
            ) | Q(
                ~Q(bbs_comment__author=request.user) & Q(
                    reply_type=1,
                    bbs_comment__is_active=True,
                    bbs_comment__article__is_active=True,
                    bbs_comment__target__is_active=True,
                    bbs_comment__parent__is_active=True,
                    bbs_comment__target__author=request.user
                )
            )
        ).order_by(
            "is_viewed",
            "-reply_time",
        ).all()

        pag = Pag()
        page_list = pag.paginate_queryset(instance, request, view=self)
        ser = ReplySerializer(page_list, many=True)
        return pag.get_paginated_response([response_code.SUCCESS_GET_REPLY_LIST, ser.data])
