from django.contrib.auth.models import AbstractUser
from rest_framework import serializers
from django.db import models


class User(AbstractUser):
    description = models.CharField(max_length=105, null=True, default=None, verbose_name="简介")
    phone = models.CharField(max_length=11, null=True, default=None, verbose_name="手机号")
    icon = models.CharField(max_length=32, default="icon/default.jpg", verbose_name="头像")
    experience = models.IntegerField(default=0, verbose_name="经验")

    fans_num = models.IntegerField(default=0, verbose_name="粉丝数")
    attention_num = models.IntegerField(default=0, verbose_name="关注数")
    up_num = models.IntegerField(default=0, verbose_name="获赞数")

    message_settings = models.OneToOneField(
        to="message.MessageSetting",
        on_delete=models.DO_NOTHING,
        verbose_name="私信设置",
        null=True,
        default=None
    )

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

    @classmethod
    def serializer(cls, field_list, *args, **kwargs):
        class UserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = field_list

        return UserSerializer(*args, **kwargs)

    @classmethod
    def is_blacked(cls, user):
        return cls.objects.black_me.filter(blacker=user).exists()

    @classmethod
    def is_black(cls, user):
        return cls.objects.my_black.filter(blacked=user).exists()


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


class UserToPermission(models.Model):
    user = models.ForeignKey(to="User", on_delete=models.DO_NOTHING)
    permission = models.ForeignKey(to="Permission", on_delete=models.DO_NOTHING)
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class Group(models.Model):
    description = models.CharField(max_length=40, null=True, default=None, verbose_name="权限组简介")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class UserToGroup(models.Model):
    user = models.ForeignKey(to="User", on_delete=models.DO_NOTHING)
    group = models.ForeignKey(to="Group", on_delete=models.DO_NOTHING)
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class GroupToPermission(models.Model):
    group = models.ForeignKey(to="Group", on_delete=models.DO_NOTHING)
    permission = models.ForeignKey(to="Permission", on_delete=models.DO_NOTHING)
    is_active = models.BooleanField(default=True, verbose_name="是否有效")


class Follow(models.Model):
    follower = models.ForeignKey(to="User", on_delete=models.DO_NOTHING, related_name="my_follow")
    followed = models.ForeignKey(to="User", on_delete=models.DO_NOTHING, related_name="follow_me")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="关注时间")

    @classmethod
    def add(cls, follower: User, followed: User):
        cls.objects.create(follower=follower, followed=followed)
        follower.attention_num += 1
        followed.fans_num += 1
        follower.save()
        followed.save()

    @classmethod
    def remove(cls, follower: User, followed: User):
        cls.objects.get(follower=follower, followed=followed).delete()
        follower.attention_num -= 1
        followed.fans_num -= 1
        follower.save()
        followed.save()


class BlackList(models.Model):
    blacker = models.ForeignKey(to="User", on_delete=models.DO_NOTHING, related_name="my_black")
    blacked = models.ForeignKey(to="User", on_delete=models.DO_NOTHING, related_name="black_me")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="拉黑时间")

    @classmethod
    def add(cls, blacker: User, blacked: User):
        cls.objects.create(blacker=blacker, blacked=blacked)

    @classmethod
    def remove(cls, blacker: User, blacked: User):
        cls.objects.get(blacker=blacker, blacked=blacked).delete()


__all__ = [
    "User",
    "Metal",
    "Follow",
    "BlackList",
]
