from backend.libs.wraps.models import APIModel, models


class Issue(APIModel):
    address = models.CharField(max_length=128, verbose_name="地址")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class IssueComment(APIModel):
    author = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="评论作者")
    issue = models.ForeignKey(to="Issue", on_delete=models.DO_NOTHING, verbose_name="对应文章")
    content = models.TextField(verbose_name="评论内容")
    comment_time = models.DateTimeField(auto_now_add=True, verbose_name="评论时间")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class IssueCommentVote(APIModel):
    author = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="点赞点踩作者")
    comment = models.ForeignKey(to="IssueComment", on_delete=models.DO_NOTHING, null=True, verbose_name="对应评论")
    is_up = models.BooleanField(verbose_name="是否点赞")
    submit_time = models.DateTimeField(auto_now=True, verbose_name="点赞点踩时间")
