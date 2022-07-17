from backend.libs.wraps.models import APIModel, models
from django.core.validators import MaxValueValidator


# Create your models here.

class Daily(APIModel):
    T = [
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
    user = models.ForeignKey(to="user.User", on_delete=models.DO_NOTHING, verbose_name="用户")
    sign = models.IntegerField(default=0, validators=[MaxValueValidator(1)], verbose_name="签到")
    bbs_post = models.IntegerField(default=0, validators=[MaxValueValidator(2)], verbose_name="发帖子")
    column_post = models.IntegerField(default=0, validators=[MaxValueValidator(5)], verbose_name="发专栏")
    answer_adopted = models.IntegerField(default=0, validators=[MaxValueValidator(5)], verbose_name="回答被采纳")
    comment = models.IntegerField(default=0, validators=[MaxValueValidator(10)], verbose_name="发评论")
    like = models.IntegerField(default=0, validators=[MaxValueValidator(10)], verbose_name="点赞")
    comment_liked = models.IntegerField(default=0, validators=[MaxValueValidator(10)], verbose_name="评论被点赞")
    post_liked = models.IntegerField(default=0, validators=[MaxValueValidator(10)], verbose_name="文章被点赞")
    commented = models.IntegerField(default=0, validators=[MaxValueValidator(10)], verbose_name="被回复")
    stared = models.IntegerField(default=0, validators=[MaxValueValidator(10)], verbose_name="被收藏")
    date = models.IntegerField(default=0, verbose_name="日期")

    def add(self, task):
        if task == "sign" and self.sign < 1:
            self.sign += 1
            self.user.experience += 50
            self.user.save()
            self.save()

        if task == "bbs_post" and self.bbs_post < 2:
            self.bbs_post += 1
            self.user.experience += 20
            self.user.save()
            self.save()

        if task == "column_post" and self.column_post < 5:
            self.column_post += 1
            self.user.experience += 50
            self.user.save()
            self.save()

        if task == "answer_adopted" and self.answer_adopted < 5:
            self.answer_adopted += 1
            self.user.experience += 50
            self.user.save()
            self.save()

        if task == "comment" and self.comment < 10:
            self.comment += 1
            self.user.experience += 10
            self.user.save()
            self.save()

        if task == "like" and self.like < 10:
            self.like += 1
            self.user.experience += 5
            self.user.save()
            self.save()

        if task == "comment_liked" and self.comment_liked < 10:
            self.comment_liked += 1
            self.user.experience += 10
            self.user.save()
            self.save()

        if task == "post_liked" and self.post_liked < 10:
            print(1)
            self.post_liked += 1
            self.user.experience += 10
            self.user.save()
            self.save()

        if task == "commented" and self.commented < 10:
            self.commented += 1
            self.user.experience += 20
            self.user.save()
            self.save()

        if task == "stared" and self.stared < 10:
            self.stared += 1
            self.user.experience += 20
            self.user.save()
            self.save()
