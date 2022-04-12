from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    description = models.CharField(max_length=40, null=True, default=None, verbose_name="简介")
    phone = models.CharField(max_length=11, null=True, default=None, verbose_name="手机号")
    icon = models.CharField(max_length=32, default="icon/default.jpg", verbose_name="头像")
    experience = models.IntegerField(default=0, verbose_name="经验")

    metal = models.ManyToManyField(
        to="Metal",
        through='UserToMetal',
        through_fields=('user', 'metal'),
    )

    group = models.ManyToManyField(
        to="Group",
        through='UserToGroup',
        through_fields=('user', 'group'),
    )

    permission = models.ManyToManyField(
        to="Permission",
        through='UserToPermission',
        through_fields=('user', 'permission'),
    )


class Metal(models.Model):
    description = models.CharField(max_length=40, null=True, default=None, verbose_name="勋章简介")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class UserToMetal(models.Model):
    user = models.ForeignKey(to="User", on_delete=models.DO_NOTHING)
    metal = models.ForeignKey(to="Metal", on_delete=models.DO_NOTHING)
    obtain_time = models.DateTimeField(auto_now_add=True, verbose_name="获取勋章时间")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class Permission(models.Model):
    description = models.CharField(max_length=40, null=True, default=None, verbose_name="权限简介")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class Group(models.Model):
    description = models.CharField(max_length=40, null=True, default=None, verbose_name="权限组简介")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class UserToPermission(models.Model):
    user = models.ForeignKey(to="User", on_delete=models.DO_NOTHING)
    permission = models.ForeignKey(to="Permission", on_delete=models.DO_NOTHING)
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class UserToGroup(models.Model):
    user = models.ForeignKey(to="User", on_delete=models.DO_NOTHING)
    group = models.ForeignKey(to="Group", on_delete=models.DO_NOTHING)
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class GroupToPermission(models.Model):
    group = models.ForeignKey(to="Group", on_delete=models.DO_NOTHING)
    permission = models.ForeignKey(to="Permission", on_delete=models.DO_NOTHING)
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class BBSReply(models.Model):
    comment = models.ForeignKey(to="bbs.Comments", on_delete=models.DO_NOTHING)

    is_article = models.BooleanField(verbose_name="是否为文章回复")
    is_viewed = models.BooleanField(default=False, verbose_name="是否已读")
    is_ignore = models.BooleanField(default=False, verbose_name="是否忽略")


__all__ = [
    "User",
    "Metal",
    "BBSReply",
]
