from rest_framework.decorators import action
from django.db.models import Q
from rest_framework.request import Request

from .serializers import *
from message.models import Dynamic, MessageSetting, Like, Reply, Origin, At
from backend.libs.constants import response_code
from backend.libs.wraps.views import APIModelViewSet
from backend.libs.wraps.response import APIResponse
from backend.libs.wraps.authenticators import CommonJwtAuthentication, UserInfoAuthentication, PermissionAuthentication


class TagView(APIModelViewSet):
    pagination_class = None
    authentication_classes = []
    queryset = Tag.objects.all().order_by("id")
    search_fields = ["name"]
    exclude = ["update", "retrieve", "destroy", "create"]
    serializer_class = TagSerializer
    code = {"list": response_code.SUCCESS_GET_TAG_LIST}


class MyColumnView(APIModelViewSet):
    authentication_classes = [PermissionAuthentication("column_author")]
    queryset = Column.objects.filter(is_active=True)
    serializer_class = MyColumnSerializer
    code = {
        "create": response_code.SUCCESS_POST_MY_COLUMN,
        "retrieve": response_code.SUCCESS_GET_MY_COLUMN,
        "update": response_code.SUCCESS_EDIT_MY_COLUMN,
        "list": response_code.SUCCESS_GET_MY_COLUMN_LIST,
        "destroy": response_code.SUCCESS_DELETE_MY_COLUMN,
    }

    def get_queryset(self):
        return self.queryset.filter(is_active=True, author=self.request.user, author__is_active=True).order_by(
            "-update_time")

    def after_create(self, instance, request, *args, **kwargs):
        if instance.is_draft:
            return

        follower_list = request.user.follow_me.exclude(
            follower__message_setting__dynamic=0,
        ).filter(
            ~Q(follower_id__in=request.user.black_me_set)
        ).all()

        create_data = map(lambda follower: Dynamic(
            sender=request.user,
            receiver=follower.follower,
            origin=Origin.SPECIAL_COLUMN,
            special_column=instance,
            is_viewed=follower.follower.message_setting.dynamic == MessageSetting.IGNORE,
        ), follower_list)

        Dynamic.objects.bulk_create(create_data)

    def after_update(self, instance, request, *args, **kwargs):
        if instance.is_draft:
            return

        if Dynamic.objects.filter(special_column=instance):
            return

        follower_list = request.user.follow_me.exclude(
            follower__message_setting__dynamic=0,
        ).filter(
            ~Q(follower_id__in=request.user.black_me_set)
        ).all()

        create_data = map(lambda follower: Dynamic(
            sender=request.user,
            receiver=follower.follower,
            origin=Origin.SPECIAL_COLUMN,
            special_column=instance,
            is_viewed=follower.follower.message_setting.dynamic == MessageSetting.IGNORE,
        ), follower_list)

        Dynamic.objects.bulk_create(create_data)

    def after_destroy(self, instance, request, *args, **kwargs):
        Dynamic.handle_delete(instance, Origin.SPECIAL_COLUMN)
        Like.handle_delete(instance, Origin.SPECIAL_COLUMN)
        Reply.handle_delete(instance, Origin.SPECIAL_COLUMN)
        At.handle_delete(instance, Origin.SPECIAL_COLUMN)


class ColumnView(APIModelViewSet):
    authentication_classes = [UserInfoAuthentication]
    queryset = Column.objects.filter(
        is_active=True,
        is_draft=False,
        is_audit=True,
        author__is_active=True
    ).order_by(
        "-comment_time"
    )
    serializer_class = ColumnSerializer
    exclude = ["update", "destroy", "create"]
    code = {
        "retrieve": response_code.SUCCESS_GET_COLUMN,
        "list": response_code.SUCCESS_GET_COLUMN_LIST,
    }

    def after_retrieve(self, instance, request, *args, **kwargs):
        if not View.objects.filter(
                column=instance,
                name_id=request.user.id
        ).exists() and not request.user.is_anonymous:
            instance.view_num += 1
            instance.save()
            View.objects.create(column=instance, name_id=request.user.id)

    @action(["POST"], True)
    def vote(self, request, pk):
        column = Column.objects.filter(id=pk, is_active=True)
        if not column:
            return APIResponse(response_code.INEXISTENT_COLUMN, "专栏不存在")

        column = column.first()
        data = request.data.copy()
        data["user_id"] = request.user.id
        data["column_id"] = pk

        ser = VoteColumnSerializer(data=data)
        ser.is_valid(True)
        ser.save()

        receiver = column.author
        sender = request.user

        if receiver != sender and receiver.message_setting.like:
            like = Like.objects.filter(special_column=column, sender=sender)
            if request.data.get("is_up") and not like:
                Like.objects.create(
                    origin=Origin.SPECIAL_COLUMN,
                    special_column_id=pk,
                    sender=sender,
                    receiver=receiver,
                    is_viewed=receiver.is_viewed(sender, "like")
                )
            else:
                like = like.first()
                like.time = datetime.datetime.now()
                like.is_active = request.data.get("is_up") and not like.is_active
                like.save()

        return APIResponse(response_code.SUCCESS_VOTE_COLUMN, "评价成功")


class CommentView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    queryset = Comment.objects.filter(
        is_active=True,
        parent_id=None,
        column__is_active=True,
        column__is_audit=True,
        column__is_draft=False
    ).order_by("-comment_time")
    serializer_class = CommentSerializer
    exclude = ["update", "retrieve"]
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
        queryset = self.queryset.filter(column_id=self.kwargs.get("column_id"))
        if self.action in ["vote", "list"]:
            return queryset

        return queryset.filter(author=self.request.user)

    @action(["POST"], True)
    def vote(self, request, column_id, pk):
        comment = Comment.objects.filter(column_id=column_id, column__is_active=True, id=pk, is_active=True)
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
            like = Like.objects.filter(origin=Origin.SPECIAL_COMMENT, special_comment=comment, sender=sender)
            if request.data.get("is_up") and not like:
                Like.objects.create(
                    origin=Origin.SPECIAL_COMMENT,
                    special_comment_id=pk,
                    sender=sender,
                    receiver=receiver,
                    is_viewed=receiver.is_viewed(sender, "like")
                )
            else:
                like = like.first()
                like.time = datetime.datetime.now()
                like.is_active = request.data.get("is_up") and not like.is_active
                like.save()

        return APIResponse(response_code.SUCCESS_VOTE_COMMENT, "评价成功")

    def after_create(self, instance: Comment, request, *args, **kwargs):
        instance.column.comment_num += 1
        instance.column.comment_time = datetime.datetime.now()
        instance.column.save()

        receiver = instance.column.author
        sender = request.user

        if receiver != sender and receiver.message_setting.reply:
            Reply.objects.create(
                origin=Origin.SPECIAL_COMMENT,
                special_comment=instance,
                sender=sender,
                receiver=receiver,
                is_viewed=receiver.is_viewed(sender, "reply")
            )

        if request.data.get("share"):
            follower_list = request.user.follow_me.exclude(
                follower__message_setting__dynamic=0,
            ).filter(
                ~Q(follower_id__in=request.user.black_me_set)
            ).all()

            create_data = map(lambda follower: Dynamic(
                sender=request.user,
                receiver=follower.follower,
                origin=Origin.SPECIAL_COMMENT,
                special_comment=instance,
                is_viewed=follower.follower.message_setting.dynamic == MessageSetting.IGNORE,
            ), follower_list)

            Dynamic.objects.bulk_create(create_data)

    def after_destroy(self, instance: Comment, request, *args, **kwargs):
        instance.column.comment_num -= 1 + instance.comment_num
        instance.column.save()

        Dynamic.handle_delete(instance, Origin.SPECIAL_COMMENT)
        Like.handle_delete(instance, Origin.SPECIAL_COMMENT)
        Reply.handle_delete(instance, Origin.SPECIAL_COMMENT)
        At.handle_delete(instance, Origin.SPECIAL_COMMENT)


class ChildrenCommentView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    queryset = Comment.objects.filter(
        is_active=True,
        parent_id__isnull=False,
        parent__is_active=True,
        column__is_active=True
    )
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
        return self.queryset.filter(parent_id=self.kwargs.get("parent_id")).order_by("id").all()

    def before_create(self, request, *args, **kwargs):
        request.data["column_id"] = kwargs.pop("column_id", None)
        request.data["parent_id"] = kwargs.pop("parent_id", None)

    def after_create(self, instance: Comment, request, *args, **kwargs):
        instance.column.comment_num += 1
        instance.column.comment_time = datetime.datetime.now()
        instance.column.save()
        instance.parent.comment_num += 1
        instance.parent.save()

        receiver = instance.target.author if instance.target else instance.parent.author
        sender = request.user

        if receiver != sender and receiver.message_setting.reply:
            Reply.objects.create(
                origin=Origin.SPECIAL_COMMENT,
                special_comment=instance,
                sender=sender,
                receiver=receiver,
                is_viewed=receiver.is_viewed(sender, "reply")
            )

        if request.data.get("share"):
            follower_list = request.user.follow_me.exclude(
                follower__message_setting__dynamic=0,
            ).filter(
                ~Q(follower_id__in=request.user.black_me_set)
            ).all()

            create_data = map(lambda follower: Dynamic(
                sender=request.user,
                receiver=follower.follower,
                origin=Origin.SPECIAL_COMMENT,
                special_comment=instance,
                is_viewed=follower.follower.message_setting.dynamic == MessageSetting.IGNORE,
            ), follower_list)

            Dynamic.objects.bulk_create(create_data)

    def after_destroy(self, instance: Comment, request, *args, **kwargs):
        instance.column.comment_num -= 1
        instance.column.save()
        instance.parent.comment_num -= 1
        instance.parent.save()

        Dynamic.handle_delete(instance, Origin.SPECIAL_COMMENT)
        Like.handle_delete(instance, Origin.SPECIAL_COMMENT)
        Reply.handle_delete(instance, Origin.SPECIAL_COMMENT)
        At.handle_delete(instance, Origin.SPECIAL_COMMENT)
