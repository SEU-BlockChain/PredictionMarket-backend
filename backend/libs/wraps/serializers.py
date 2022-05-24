from rest_framework import serializers
from user.models import User, Metal
from rest_framework_jwt.serializers import jwt_payload_handler, jwt_encode_handler


class EmptySerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class APIModelSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.after_create(validated_data, self)
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.after_update(validated_data, self)
        return instance


class MetalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metal
        fields = [
            "id",
            "description"
        ]


class UserSerializer(serializers.ModelSerializer):
    metal = MetalSerializer(many=True)
    token = serializers.SerializerMethodField()

    def get_token(self, instance):
        payload = jwt_payload_handler(instance)
        token = jwt_encode_handler(payload)
        return token

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "date_joined",
            "phone",
            "icon",
            "description",
            "experience",
            "metal",
            "is_staff",
            "up_num",
            "attention_num",
            "fans_num",
            "token"
        ]


class OtherUserSerializer(serializers.ModelSerializer):
    metal = MetalSerializer(many=True)
    followed = serializers.SerializerMethodField()
    follower = serializers.SerializerMethodField()

    def get_followed(self, instance: User):
        user = self.context["request"].user
        if user.is_anonymous:
            return None

        return user.my_follow.filter(followed=instance).exists()

    def get_follower(self, instance: User):
        user = self.context["request"].user
        if user.is_anonymous:
            return None

        return user.follow_me.filter(follower=instance).exists()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "icon",
            "description",
            "experience",
            "metal",
            "up_num",
            "attention_num",
            "fans_num",
            "followed",
            "follower"
        ]

