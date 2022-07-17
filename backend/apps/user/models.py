from django.contrib.auth.models import AbstractUser
from django.db import models
from message.models import MessageSetting
from backend.libs.function.get import getDate
from task.models import Daily


class User(AbstractUser):
    description = models.CharField(max_length=105, null=True, default=None, verbose_name="简介")
    phone = models.CharField(max_length=11, null=True, default=None, verbose_name="手机号")
    icon = models.CharField(max_length=32, default="icon/default.jpg", verbose_name="头像")
    experience = models.IntegerField(default=0, verbose_name="经验")

    fans_num = models.IntegerField(default=0, verbose_name="粉丝数")
    attention_num = models.IntegerField(default=0, verbose_name="关注数")
    up_num = models.IntegerField(default=0, verbose_name="获赞数")

    message_setting = models.OneToOneField(
        to="message.MessageSetting",
        on_delete=models.DO_NOTHING,
        verbose_name="私信设置",
        default=None,
        null=True
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

    def __init__(self, *args, **kwargs):
        self._permission_set = None
        self._my_black_set = None
        self._black_me_set = None
        self._my_follow_set = None
        self._follow_me_set = None
        super().__init__(*args, **kwargs)

    @property
    def permission_set(self):
        if self._permission_set is None:
            a = []
            for i in self.permission.filter(is_active=True).all():
                a.append(i.description)
            for i in self.group.filter(is_active=True).all():
                for j in i.permission.filter(is_active=True).all():
                    a.append(j.description)
            self._permission_set = set(a) if a else set()
        return self._permission_set

    def has_permission(self, permission):
        return permission in self.permission_set

    @classmethod
    def is_blacked(cls, user):
        return cls.objects.black_me.filter(blacker=user).exists()

    @classmethod
    def is_black(cls, user):
        return cls.objects.my_black.filter(blacked=user).exists()

    @property
    def my_black_set(self):
        if self._my_black_set is None:
            if self.is_anonymous:
                self._my_black_set = set()
            else:
                self._my_black_set = set(map(lambda x: x[0], self.my_black.values_list('blacked'))) or set()
        return self._my_black_set

    @property
    def black_me_set(self):
        if self._black_me_set is None:
            if self.is_anonymous:
                self._black_me_set = set()
            else:
                self._black_me_set = set(map(lambda x: x[0], self.black_me.values_list('blacker'))) or set()
        return self._black_me_set

    @property
    def my_follow_set(self):
        if self._my_follow_set is None:
            if self.is_anonymous:
                self._my_follow_set = set()
            else:
                self._my_follow_set = set(map(lambda x: x[0], self.my_follow.values_list('followed'))) or set()
        return self._my_follow_set

    @property
    def follow_me_set(self):
        if self._follow_me_set is None:
            if self.is_anonymous:
                self._follow_me_set = set()
            else:
                self._follow_me_set = set(map(lambda x: x[0], self.follow_me.values_list('follower'))) or set()
        return self._follow_me_set

    def is_viewed(self, sender, category):
        setting = getattr(self.message_setting, category)
        if setting == MessageSetting.IGNORE:
            return True

        if setting == MessageSetting.FOLLOWED:
            return sender.id not in self.my_follow_set - self.my_black_set

        return False

    @property
    def daily(self) -> Daily:
        today = getDate()
        record = Daily.objects.filter(user=self, date=today).first()
        if not record:
            record = Daily.objects.create(user=self, date=today)

        return record


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
    permission = models.ManyToManyField(
        to="Permission",
        through='GroupToPermission',
        through_fields=('group', 'permission'),
    )


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
