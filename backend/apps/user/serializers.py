import re
import time

from django.core.cache import cache
from django.db.models import Q

from .models import *
from message.models import MessageSetting, System
from backend.libs.wraps.serializers import EmptySerializer, OtherUserSerializer, serializers
from backend.libs.constants import re_patterns, response_code
from backend.libs.wraps.errors import SerializerError


class UsernameRegisterSerializer(EmptySerializer):
    username = serializers.CharField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate_username(self, username):
        if not re.search(re_patterns.USERNAME, username):
            raise SerializerError("非法的用户名", response_code.INVALID_USERNAME)

        if User.objects.filter(username=username).exists():
            raise SerializerError("用户名已注册", response_code.USERNAME_REGISTERED)

        return username

    def validate_password(self, password):
        if not re.search(re_patterns.PASSWORD, password):
            raise SerializerError("非法的密码", response_code.INVALID_PASSWORD)

        return password

    def validate_confirm_password(self, confirm_password):
        if not re.search(re_patterns.PASSWORD, confirm_password):
            raise SerializerError("非法的确认密码", response_code.INVALID_PASSWORD)

        return confirm_password

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.pop("confirm_password", None)
        if password != confirm_password:
            raise SerializerError("密码与确认密码不一致", response_code.INCONSISTENT_PASSWORD)

        return attrs

    def create(self, validated_data):
        validated_data["message_setting"] = MessageSetting.objects.create()
        user = User.objects.create_user(**validated_data)
        System.objects.create(receiver=user, content="<p>欢迎注册!</p>")
        return user


class PhoneRegisterSerializer(EmptySerializer):
    phone = serializers.CharField()
    code = serializers.CharField()

    def validate_phone(self, phone):
        if not re.search(re_patterns.PHONE, phone):
            raise SerializerError("无效的手机号码", response_code.INVALID_PHONE)

        return phone

    def validate_code(self, code):
        if not re.search(re_patterns.CODE, code):
            raise SerializerError("验证码为4位数字", response_code.INCORRECT_CODE_FORM)

        return code

    def validate(self, attrs):
        code = attrs.get("code")
        phone = attrs.get("phone")
        if code != cache.get("register" + phone):
            raise SerializerError("验证码错误", response_code.INCORRECT_CODE)

        attrs.pop("code")
        attrs["password"] = phone
        attrs["username"] = str(int(time.time()))
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(EmptySerializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate_username(self, username):
        if not re.search("|".join([re_patterns.USERNAME, re_patterns.PHONE]), username):
            raise SerializerError("非法的用户名", response_code.INVALID_USERNAME)

        return username

    def validate_password(self, password):
        if not re.search("|".join([re_patterns.PASSWORD, re_patterns.CODE]), password):
            raise SerializerError("非法的密码", response_code.INVALID_PASSWORD)

        return password

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")
        user = User.objects.filter(Q(username=username) | Q(phone=username), is_active=True).first()
        if not user:
            raise SerializerError("用户不存在", response_code.USERNAME_NOT_REGISTERED)

        if not (user.check_password(password) or password == cache.get("login" + username)):
            raise SerializerError("密码错误", response_code.INCORRECT_PASSWORD)

        self.context["user"] = user

        return attrs


class ResetPasswordSerializer(EmptySerializer):
    phone = serializers.CharField()
    code = serializers.CharField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate_phone(self, phone):
        if not re.search(re_patterns.PHONE, phone):
            raise SerializerError("无效的电话号码", response_code.INVALID_PHONE)

        is_register = User.objects.filter(phone=phone).exists()
        if not is_register:
            raise SerializerError("手机号未绑定账号", response_code.NOT_REGISTERED)

        return phone

    def validate_code(self, code):
        if not re.search(re_patterns.CODE, code):
            raise SerializerError("验证码格式错误", response_code.INCORRECT_CODE_FORM)

        return code

    def validate_password(self, password):
        if not re.search(re_patterns.PASSWORD, password):
            raise SerializerError("非法的密码", response_code.INVALID_PASSWORD)

        return password

    def validate_confirm_password(self, confirm_password):
        if not re.search(re_patterns.PASSWORD, confirm_password):
            raise SerializerError("非法的确认密码", response_code.INVALID_PASSWORD)

        return confirm_password

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")
        if password != confirm_password:
            raise SerializerError("密码与确认密码不一致", response_code.INCONSISTENT_PASSWORD)

        phone = attrs.get("phone")
        code = attrs.get("code")
        if code != cache.get("reset_password" + phone):
            raise SerializerError("验证码错误", response_code.INCORRECT_CODE)

        return attrs

    def update(self, instance, validated_data):
        phone = validated_data.get("phone")
        password = validated_data.get("password")

        user = instance.filter(phone=phone).first()
        user.set_password(password)
        user.save()
        return user


class ChangePasswordSerializer(EmptySerializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate_old_password(self, old_password):
        if not re.search(re_patterns.PASSWORD, old_password):
            raise SerializerError("非法的密码", response_code.INVALID_PASSWORD)

        return old_password

    def validate_new_password(self, old_new_password):
        if not re.search(re_patterns.PASSWORD, old_new_password):
            raise SerializerError("非法的密码", response_code.INVALID_PASSWORD)

        return old_new_password

    def validate_confirm_password(self, confirm_password):
        if not re.search(re_patterns.PASSWORD, confirm_password):
            raise SerializerError("非法的密码", response_code.INVALID_PASSWORD)

        return confirm_password

    def validate(self, attrs):
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")
        if new_password != confirm_password:
            raise SerializerError("密码与确认密码不一致", response_code.INCONSISTENT_PASSWORD)

        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data.get("new_password"))
        instance.save()
        return instance


class BindPhoneView(EmptySerializer):
    phone = serializers.CharField()
    code = serializers.CharField()

    def validate_phone(self, phone):
        if not re.search(re_patterns.PHONE, phone):
            raise SerializerError("无效的电话号码", response_code.INVALID_PHONE)

        is_register = User.objects.filter(phone=phone).exists()
        if is_register:
            raise SerializerError("手机号已绑定账号", response_code.REGISTERED)

        return phone

    def validate_code(self, code):
        if not re.search(re_patterns.CODE, code):
            raise SerializerError("验证码格式错误", response_code.INCORRECT_CODE_FORM)

        return code

    def validate(self, attrs):
        phone = attrs.get("phone")
        code = attrs.get("code")
        if code != cache.get("bind_phone" + phone):
            raise SerializerError("验证码错误", response_code.INCORRECT_CODE)

        return attrs

    def update(self, instance, validated_data):
        phone = validated_data.get("phone")

        instance.phone = phone
        instance.save()

        return instance


class UnbindPhoneView(EmptySerializer):
    phone = serializers.CharField()
    code = serializers.CharField()

    def validate_phone(self, phone):
        if not re.search(re_patterns.PHONE, phone):
            raise SerializerError("无效的电话号码", response_code.INVALID_PHONE)

        is_register = User.objects.filter(phone=phone).exists()
        if not is_register:
            raise SerializerError("手机号未绑定账号", response_code.REGISTERED)

        return phone

    def validate_code(self, code):
        if not re.search(re_patterns.CODE, code):
            raise SerializerError("验证码格式错误", response_code.INCORRECT_CODE_FORM)

        return code

    def validate(self, attrs):
        phone = attrs.get("phone")
        code = attrs.get("code")
        if code != cache.get("unbind_phone" + phone):
            raise SerializerError("验证码错误", response_code.INCORRECT_CODE)

        return attrs

    def update(self, instance, validated_data):
        instance.phone = None
        instance.save()

        return instance


class UserInfoSerializer(EmptySerializer):
    username = serializers.CharField(required=False)
    description = serializers.CharField(max_length=100, required=False)

    def validate_username(self, username):
        is_register = User.objects.filter(username=username).exists()
        if is_register:
            raise SerializerError("用户名已注册", response_code.USERNAME_REGISTERED)

        if not re.search(re_patterns.USERNAME, username):
            raise SerializerError("非法的用户名", response_code.INVALID_USERNAME)
        return username

    def update(self, instance, validated_data):
        username = validated_data.get("username")
        description = validated_data.get("description")
        if username:
            instance.username = username
        if description:
            instance.description = description
        instance.save()

        return instance


class FollowSerializer(serializers.ModelSerializer):
    followed = serializers.SerializerMethodField()
    follower = serializers.SerializerMethodField()

    def get_followed(self, instance: Follow):
        return OtherUserSerializer(instance.followed, context=self.context).data

    def get_follower(self, instance: Follow):
        return OtherUserSerializer(instance.follower, context=self.context).data

    class Meta:
        model = Follow
        fields = [
            "id",
            "follower",
            "followed",
            "create_time"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        action = self.context["view"].action
        if action == "as_follower":
            self.fields.pop("follower")
        elif action == "as_followed":
            self.fields.pop("followed")


class BlackListSerializer(serializers.ModelSerializer):
    blacked = serializers.SerializerMethodField()

    def get_blacked(self, instance: BlackList):
        return OtherUserSerializer(instance.blacked, context=self.context).data

    class Meta:
        model = BlackList
        fields = [
            "id",
            "blacked",
            "create_time"
        ]

