from backend.libs.wraps.models import APIModel, models
import datetime
from message.models import At, Origin
from user.models import User


class Draft(APIModel):
    title = models.CharField(max_length=64, verbose_name="文章标题")
    author = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="文章作者")
    category = models.ForeignKey(to="Category", on_delete=models.DO_NOTHING, verbose_name="文章类别")
    raw_content = models.TextField(verbose_name="文章内容原始数据")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class Article(APIModel):
    title = models.CharField(max_length=32, verbose_name="文章标题")
    author = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="文章作者")
    category = models.ForeignKey(to="Category", on_delete=models.DO_NOTHING, verbose_name="文章类别")
    description = models.TextField(verbose_name="文章摘要")
    content = models.TextField(verbose_name="文章内容")
    raw_content = models.TextField(verbose_name="文章内容原始数据")
    top = models.IntegerField(default=None, null=True, verbose_name="置顶顺序")

    view_num = models.IntegerField(default=0, verbose_name="浏览数")
    up_num = models.IntegerField(default=0, verbose_name="点赞数")
    down_num = models.IntegerField(default=0, verbose_name="点踩数")
    comment_num = models.IntegerField(default=0, verbose_name="评论数")

    create_time = models.DateTimeField(auto_now_add=True, verbose_name="发帖时间")
    update_time = models.DateTimeField(default=datetime.datetime.now, verbose_name="最后更新时间")
    comment_time = models.DateTimeField(default=datetime.datetime.now, verbose_name="最后回复时间")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")

    def after_create(self, validated_data, serializer):
        mention = serializer.context["mention"]
        sender: User = serializer.context["request"].user

        sender.daily.add("bbs_post")

        create_data = []
        for receiver in mention:
            if receiver != sender and receiver.message_setting.at and receiver.id not in sender.black_me_set:
                create_data.append(At(
                    sender=sender,
                    receiver=receiver,
                    origin=Origin.BBS_ARTICLE,
                    bbs_article=self,
                    is_viewed=receiver.is_viewed(sender, "at")
                ))
        At.objects.bulk_create(create_data)


class Comment(APIModel):
    author = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="评论作者")
    article = models.ForeignKey(to="Article", on_delete=models.DO_NOTHING, verbose_name="对应文章")
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

        sender.daily.add("comment")
        if self.target:
            self.parent.author.daily.add("commented")
        else:
            self.article.author.daily.add("commented")

        create_data = []
        for receiver in mention:
            if receiver != sender and receiver.message_setting.at and receiver.id not in sender.black_me_set:
                create_data.append(At(
                    sender=sender,
                    receiver=receiver,
                    origin=Origin.BBS_COMMENT,
                    bbs_comment=self,
                    is_viewed=receiver.is_viewed(sender, "at")
                ))
        At.objects.bulk_create(create_data)


class Category(APIModel):
    category = models.CharField(max_length=16, verbose_name="分类名")
    description = models.TextField(verbose_name="描述", default="暂无介绍~")
    icon = models.CharField(max_length=64, default=None, verbose_name="首页icon")
    icon_detail = models.CharField(max_length=64, default=None, verbose_name="详情icon")
    stuff = models.BooleanField(default=False, verbose_name="仅官方")
    top = models.IntegerField(default=0, verbose_name="展示优先级")


class View(APIModel):
    name = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="浏览者")
    view_time = models.DateTimeField(auto_now_add=True, verbose_name="浏览时间")
    article = models.ForeignKey(to="Article", on_delete=models.DO_NOTHING, verbose_name="浏览帖子")


class UpAndDown(APIModel):
    author = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="点赞点踩作者")
    article = models.ForeignKey(to="Article", on_delete=models.DO_NOTHING, null=True, verbose_name="对应文章")
    comment = models.ForeignKey(to="Comment", on_delete=models.DO_NOTHING, null=True, verbose_name="对应评论")
    is_up = models.BooleanField(verbose_name="是否点赞")
    submit_time = models.DateTimeField(auto_now=True, verbose_name="点赞点踩时间")


class Collection(APIModel):
    author = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="合集作者")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    title = models.CharField(max_length=50, verbose_name="合集描述")
    description = models.CharField(max_length=200, verbose_name="合集描述")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")

    article = models.ManyToManyField(
        to="Article",
        through='CollectionToArticle',
        through_fields=('collection', 'article'),
    )


class CollectionToArticle(APIModel):
    collection = models.ForeignKey(to="Collection", on_delete=models.DO_NOTHING, verbose_name="对应合集")
    article = models.ForeignKey(to="Article", on_delete=models.DO_NOTHING, verbose_name="对应文章")
    top = models.IntegerField(verbose_name="顺序")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")
