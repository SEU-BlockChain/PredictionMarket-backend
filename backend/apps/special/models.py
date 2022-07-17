import datetime

from backend.libs.wraps.models import APIModel, models
from user.models import User
from message.models import At, Origin


class Column(APIModel):
    author = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="专栏作者")
    title = models.CharField(max_length=32, verbose_name="专栏标题")
    description = models.TextField(max_length=128, verbose_name="简介")
    content = models.TextField(verbose_name="专栏内容")
    raw_content = models.TextField(verbose_name="专栏内容原始数据")
    menu = models.TextField(verbose_name="目录")
    top = models.IntegerField(default=None, null=True, verbose_name="置顶顺序")

    view_num = models.IntegerField(default=0, verbose_name="浏览数")
    up_num = models.IntegerField(default=0, verbose_name="点赞数")
    down_num = models.IntegerField(default=0, verbose_name="点踩数")
    comment_num = models.IntegerField(default=0, verbose_name="评论数")

    create_time = models.DateTimeField(auto_now_add=True, verbose_name="发帖时间")
    update_time = models.DateTimeField(default=datetime.datetime.now, verbose_name="最后更新时间")
    comment_time = models.DateTimeField(default=datetime.datetime.now, verbose_name="最后回复时间")

    is_draft = models.BooleanField(verbose_name="是否为草稿")
    is_audit = models.BooleanField(default=True, verbose_name="是否已审核")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")

    tag = models.ManyToManyField(
        to="Tag",
        through='ColumnToTag',
        through_fields=('column', 'tag'),
    )


class Tag(APIModel):
    name = models.CharField(max_length=16, verbose_name="标签")


class Comment(APIModel):
    author = models.ForeignKey(
        to="user.User",
        on_delete=models.DO_NOTHING,
        verbose_name="评论作者",
        related_name="column_comment"
    )
    column = models.ForeignKey(
        to="Column",
        on_delete=models.DO_NOTHING,
        verbose_name="对应专栏",
    )
    content = models.TextField(verbose_name="评论内容")
    description = models.TextField(verbose_name="评论摘要")
    up_num = models.IntegerField(default=0, verbose_name="点赞数")
    down_num = models.IntegerField(default=0, verbose_name="点踩数")
    comment_num = models.IntegerField(default=0, verbose_name="评论数")
    comment_time = models.DateTimeField(auto_now_add=True, verbose_name="评论时间")
    parent = models.ForeignKey(to="self", on_delete=models.DO_NOTHING, null=True, verbose_name="所属评论",
                               related_name="parent_comments")
    target = models.ForeignKey(to="self", on_delete=models.DO_NOTHING, null=True, verbose_name="对应评论",
                               related_name="target_comments")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")

    def after_create(self, validated_data, serializer):
        mention = serializer.context["mention"]
        sender: User = serializer.context["request"].user

        create_data = []
        for receiver in mention:
            if receiver != sender and receiver.message_setting.at and receiver.id not in sender.black_me_set:
                create_data.append(At(
                    sender=sender,
                    receiver=receiver,
                    origin=Origin.SPECIAL_COMMENT,
                    special_comment=self,
                    is_viewed=receiver.is_viewed(sender, "at")
                ))
        At.objects.bulk_create(create_data)


class View(APIModel):
    name = models.ForeignKey(
        to="user.User",
        on_delete=models.DO_NOTHING,
        verbose_name="浏览者",
        related_name="column_view"
    )
    view_time = models.DateTimeField(auto_now_add=True, verbose_name="浏览时间")
    column = models.ForeignKey(to="Column", on_delete=models.DO_NOTHING, verbose_name="浏览专栏")


class UpAndDown(APIModel):
    author = models.ForeignKey(
        to="user.User",
        on_delete=models.DO_NOTHING,
        verbose_name="点赞点踩作者",
        related_name="column_up_and_down"
    )
    column = models.ForeignKey(to="Column", on_delete=models.DO_NOTHING, null=True, verbose_name="对应专栏")
    comment = models.ForeignKey(to="Comment", on_delete=models.DO_NOTHING, null=True, verbose_name="对应评论")
    is_up = models.BooleanField(verbose_name="是否点赞")
    submit_time = models.DateTimeField(auto_now=True, verbose_name="点赞点踩时间")


class ColumnToTag(APIModel):
    column = models.ForeignKey(to="Column", on_delete=models.DO_NOTHING)
    tag = models.ForeignKey(to="Tag", on_delete=models.DO_NOTHING)
