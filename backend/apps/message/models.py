from backend.libs.wraps.models import APIModel, models
from functools import partial

from django.db.models import Q

UserField = partial(models.ForeignKey, to="user.User", on_delete=models.DO_NOTHING)


class Origin:
    BBS_ARTICLE = 0
    BBS_COMMENT = 1
    SPECIAL_COLUMN = 2
    SPECIAL_COMMENT = 3
    ISSUE_COMMENT = 4


class AbstractMessage(APIModel):
    is_viewed = models.BooleanField(default=False, verbose_name="是否已读")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")
    time = models.DateTimeField(auto_now_add=True, verbose_name="消息时间")

    class Meta:
        abstract = True


class AbstractOrigin(APIModel):
    STATUS_CHOICES = [
        (Origin.BBS_ARTICLE, "论坛文章"),
        (Origin.BBS_COMMENT, "论坛评论"),
        (Origin.SPECIAL_COLUMN, "专栏帖子"),
        (Origin.SPECIAL_COMMENT, "专栏评论")
    ]
    origin = models.IntegerField(choices=STATUS_CHOICES, null=True, default=None, verbose_name="来源")

    bbs_article = models.ForeignKey(to="bbs.Article", null=True, default=None, on_delete=models.DO_NOTHING)
    bbs_comment = models.ForeignKey(to="bbs.Comment", null=True, default=None, on_delete=models.DO_NOTHING)

    special_column = models.ForeignKey(to="special.Column", null=True, default=None, on_delete=models.DO_NOTHING)
    special_comment = models.ForeignKey(to="special.Comment", null=True, default=None, on_delete=models.DO_NOTHING)

    issue_comment = models.ForeignKey(to="issue.IssueComment", null=True, default=None, on_delete=models.DO_NOTHING)

    class Meta:
        abstract = True


class Reply(AbstractMessage, AbstractOrigin):
    sender = UserField(verbose_name="发信人", related_name="my_reply")
    receiver = UserField(verbose_name="收信人", related_name="reply_me")

    @classmethod
    def handle_delete(cls, instance, category):
        if category == Origin.BBS_ARTICLE:
            queryset = cls.objects.filter(
                bbs_comment__article=instance,
                is_active=True,
            ).all()
        elif category == Origin.BBS_COMMENT:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.BBS_COMMENT,
                    bbs_comment__parent=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.BBS_COMMENT,
                    bbs_comment__target=instance,
                    is_active=True
                )
            ).all()
        elif category == Origin.SPECIAL_COLUMN:
            queryset = cls.objects.filter(
                special_comment__column=instance,
                is_active=True,
            ).all()
        elif category == Origin.SPECIAL_COMMENT:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.SPECIAL_COMMENT,
                    special_comment__parent=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.SPECIAL_COMMENT,
                    special_comment__target=instance,
                    is_active=True
                )
            ).all()
        elif category == Origin.ISSUE_COMMENT:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.ISSUE_COMMENT,
                    issue_comment__parent=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.ISSUE_COMMENT,
                    issue_comment__target=instance,
                    is_active=True
                )
            ).all()
        else:
            return

        for i in queryset:
            i.is_active = False
        cls.objects.bulk_update(queryset, ["is_active"])


class At(AbstractMessage, AbstractOrigin):
    sender = UserField(verbose_name="发信人", related_name="my_at")
    receiver = UserField(verbose_name="收信人", related_name="at_me")

    @classmethod
    def handle_delete(cls, instance, category):
        if category == Origin.BBS_ARTICLE:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.BBS_ARTICLE,
                    bbs_article=instance,
                    is_active=True,
                ) | Q(
                    origin=Origin.BBS_COMMENT,
                    bbs_comment__article=instance,
                    is_active=True,
                )
            ).all()
        elif category == Origin.BBS_COMMENT:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.BBS_COMMENT,
                    bbs_comment__parent=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.BBS_COMMENT,
                    bbs_comment__target=instance,
                    is_active=True
                )
            ).all()
        elif category == Origin.SPECIAL_COLUMN:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.SPECIAL_COLUMN,
                    special_column=instance,
                    is_active=True,
                ) | Q(
                    origin=Origin.SPECIAL_COMMENT,
                    special_comment__column=instance,
                    is_active=True,
                )
            ).all()
        elif category == Origin.SPECIAL_COMMENT:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.SPECIAL_COMMENT,
                    special_comment__parent=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.SPECIAL_COMMENT,
                    special_comment__target=instance,
                    is_active=True
                )
            ).all()
        elif category == Origin.ISSUE_COMMENT:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.ISSUE_COMMENT,
                    issue_comment__parent=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.ISSUE_COMMENT,
                    issue_comment__target=instance,
                    is_active=True
                )
            ).all()
        else:
            return

        for i in queryset:
            i.is_active = False
        cls.objects.bulk_update(queryset, ["is_active"])


class Like(AbstractMessage, AbstractOrigin):
    sender = UserField(verbose_name="发信人", related_name="my_like")
    receiver = UserField(verbose_name="收信人", related_name="like_me")

    @classmethod
    def handle_delete(cls, instance, category):
        if category == Origin.BBS_ARTICLE:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.BBS_ARTICLE,
                    bbs_article=instance,
                    is_active=True,
                ) | Q(
                    origin=Origin.BBS_COMMENT,
                    bbs_comment__article=instance,
                    is_active=True
                )
            ).all()
        elif category == Origin.BBS_COMMENT:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.BBS_COMMENT,
                    bbs_comment=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.BBS_COMMENT,
                    bbs_comment__parent=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.BBS_COMMENT,
                    bbs_comment__target=instance,
                    is_active=True
                )
            ).all()
        elif category == Origin.SPECIAL_COLUMN:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.SPECIAL_COLUMN,
                    special_column=instance,
                    is_active=True,
                ) | Q(
                    origin=Origin.SPECIAL_COMMENT,
                    special_comment__column=instance,
                    is_active=True
                )
            ).all()
        elif category == Origin.SPECIAL_COMMENT:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.SPECIAL_COMMENT,
                    special_column=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.SPECIAL_COMMENT,
                    special_comment__parent=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.SPECIAL_COMMENT,
                    special_comment__target=instance,
                    is_active=True
                )
            ).all()
        elif category == Origin.ISSUE_COMMENT:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.ISSUE_COMMENT,
                    issue_comment=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.ISSUE_COMMENT,
                    issue_comment__parent=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.ISSUE_COMMENT,
                    issue_comment__target=instance,
                    is_active=True
                )
            ).all()
        else:
            return

        for i in queryset:
            i.is_active = False
        cls.objects.bulk_update(queryset, ["is_active"])


class System(AbstractMessage):
    receiver = UserField(verbose_name="收信人", related_name="system_me")
    content = models.TextField(verbose_name="通知详情")


class Private(AbstractMessage):
    sender = UserField(verbose_name="发信人", related_name="my_private")
    receiver = UserField(verbose_name="收信人", related_name="private_me")
    content = models.CharField(max_length=256, verbose_name="消息详情")


class Dynamic(AbstractMessage, AbstractOrigin):
    sender = UserField(verbose_name="发信人", related_name="my_dynamic")
    receiver = UserField(verbose_name="收信人", related_name="dynamic_me")

    @classmethod
    def handle_delete(cls, instance, category):
        if category == Origin.BBS_ARTICLE:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.BBS_ARTICLE,
                    bbs_article=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.BBS_COMMENT,
                    bbs_comment__article=instance,
                    is_active=True
                )
            ).all()
        elif category == Origin.BBS_COMMENT:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.BBS_COMMENT,
                    bbs_comment=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.BBS_COMMENT,
                    bbs_comment__parent=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.BBS_COMMENT,
                    bbs_comment__target=instance,
                    is_active=True
                )
            ).all()
        elif category == Origin.SPECIAL_COLUMN:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.SPECIAL_COLUMN,
                    special_column=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.SPECIAL_COMMENT,
                    special_comment__column=instance,
                    is_active=True
                )
            ).all()
        elif category == Origin.SPECIAL_COMMENT:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.SPECIAL_COMMENT,
                    special_column=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.SPECIAL_COMMENT,
                    special_comment__parent=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.SPECIAL_COMMENT,
                    special_comment__target=instance,
                    is_active=True
                )
            ).all()
        elif category == Origin.ISSUE_COMMENT:
            queryset = cls.objects.filter(
                Q(
                    origin=Origin.ISSUE_COMMENT,
                    issue_comment=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.ISSUE_COMMENT,
                    issue_comment__parent=instance,
                    is_active=True
                ) | Q(
                    origin=Origin.ISSUE_COMMENT,
                    issue_comment__target=instance,
                    is_active=True
                )
            ).all()
        else:
            return

        for i in queryset:
            i.is_active = False
        cls.objects.bulk_update(queryset, ["is_active"])


class MessageSetting(APIModel):
    FORBID = 0
    IGNORE = 1
    FOLLOWED = 2
    RECEIVE = 3
    STATUS_CHOICES = [
        (FORBID, "全部拒收"),
        (IGNORE, "接收但不提醒"),
        (FOLLOWED, "接收但只提醒我关注的"),
        (RECEIVE, "接收并提醒"),
    ]
    reply = models.IntegerField(choices=STATUS_CHOICES, default=RECEIVE, verbose_name="回复消息提醒")
    at = models.IntegerField(choices=STATUS_CHOICES, default=RECEIVE, verbose_name="@消息提醒")
    like = models.IntegerField(choices=STATUS_CHOICES, default=RECEIVE, verbose_name="点赞消息提醒")
    system = models.IntegerField(choices=STATUS_CHOICES, default=RECEIVE, verbose_name="系统消息提醒")
    private = models.IntegerField(choices=STATUS_CHOICES, default=RECEIVE, verbose_name="私信消息提醒")
    dynamic = models.IntegerField(choices=STATUS_CHOICES, default=RECEIVE, verbose_name="动态消息提醒")
