from backend.libs.wraps.models import APIModel, models


class Vote(APIModel):
    title = models.CharField(max_length=128, verbose_name="题目")
    creator = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="创建人")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    start_time = models.DateTimeField(verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间")
    min_num = models.IntegerField(verbose_name="最少选择")
    max_num = models.IntegerField(verbose_name="最多选择")
    anonymous = models.BooleanField(verbose_name="是否允许匿名")
    need_vote = models.BooleanField(verbose_name="是否投票后才能查看结果")
    is_active = models.BooleanField(verbose_name="是否有效", default=True)

    voter = models.ManyToManyField(
        to="user.User",
        through="VoteToUser",
        through_fields=("vote", "user"),
        related_name="my_vote"
    )


class VoteChoice(APIModel):
    content = models.CharField(max_length=128, verbose_name="选项")

    vote = models.ForeignKey(to="Vote", on_delete=models.DO_NOTHING, default=None, verbose_name="对应投票")

    voter = models.ManyToManyField(
        to="user.User",
        through="ChoiceToUser",
        through_fields=("choice", "user")
    )


class VoteToUser(APIModel):
    vote = models.ForeignKey(to="Vote", on_delete=models.DO_NOTHING)
    user = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING)
    vote_time = models.DateTimeField(auto_now_add=True, verbose_name="投票时间")


class ChoiceToUser(APIModel):
    choice = models.ForeignKey(to="VoteChoice", on_delete=models.DO_NOTHING)
    user = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING)
