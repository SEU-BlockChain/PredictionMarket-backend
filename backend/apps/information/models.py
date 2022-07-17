from backend.libs.wraps.models import APIModel, models
import datetime


class News(APIModel):
    title = models.CharField(max_length=64, verbose_name="资讯标题")
    author = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="文章作者")
    description = models.TextField(verbose_name="资讯摘要")
    content = models.TextField(verbose_name="资讯内容")
    raw_content = models.TextField(verbose_name="资讯内容原始数据")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="发帖时间")
    update_time = models.DateTimeField(default=datetime.datetime.now, verbose_name="最后更新时间")
    is_draft = models.BooleanField(default=True, verbose_name="是否为草稿")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")
