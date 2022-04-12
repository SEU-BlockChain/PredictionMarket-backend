from django.db import models


class Articles(models.Model):
    title = models.CharField(max_length=32, verbose_name="文章标题")
    author = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="文章作者")
    category = models.ForeignKey(to="Categories", on_delete=models.DO_NOTHING, verbose_name="文章类别")
    description = models.TextField(verbose_name="文章摘要")
    content = models.TextField(verbose_name="文章内容")
    raw_content = models.TextField(verbose_name="文章内容原始数据")

    view_num = models.IntegerField(default=0, verbose_name="浏览数")
    up_num = models.IntegerField(default=0, verbose_name="点赞数")
    down_num = models.IntegerField(default=0, verbose_name="点踩数")
    comment_num = models.IntegerField(default=0, verbose_name="评论数")

    create_time = models.DateTimeField(auto_now_add=True, verbose_name="发帖时间")
    update_time = models.DateTimeField(null=True, default=None, verbose_name="最后更新时间")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class Comments(models.Model):
    author = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="评论作者")
    article = models.ForeignKey(to="Articles", on_delete=models.DO_NOTHING, verbose_name="对应文章")
    content = models.CharField(max_length=256, verbose_name="评论内容")
    up_num = models.IntegerField(default=0, verbose_name="点赞数")
    down_num = models.IntegerField(default=0, verbose_name="点踩数")
    comment_num = models.IntegerField(default=0, verbose_name="评论数")
    comment_time = models.DateTimeField(auto_now_add=True, verbose_name="评论时间")
    parent = models.ForeignKey(to="self", on_delete=models.DO_NOTHING, null=True, verbose_name="所属评论",
                               related_name="parent_comments")
    target = models.ForeignKey(to="self", on_delete=models.DO_NOTHING, null=True, verbose_name="对应评论",
                               related_name="target_comments")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class Categories(models.Model):
    category = models.CharField(max_length=16, verbose_name="分类名")


class Views(models.Model):
    name = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="浏览者")
    view_time = models.DateTimeField(auto_now_add=True, verbose_name="浏览时间")
    article = models.ForeignKey(to="Articles", on_delete=models.DO_NOTHING, verbose_name="浏览帖子")


class UpAndDowns(models.Model):
    author = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="点赞点踩作者")
    article = models.ForeignKey(to="Articles", on_delete=models.DO_NOTHING, null=True, verbose_name="对应文章")
    comment = models.ForeignKey(to="Comments", on_delete=models.DO_NOTHING, null=True, verbose_name="对应评论")
    is_up = models.BooleanField(verbose_name="是否点赞")
    submit_time = models.DateTimeField(auto_now=True, verbose_name="点赞点踩时间")


__all__ = [
    "Articles",
    "Comments",
    "Categories",
    "UpAndDowns",
    "Views",
]
