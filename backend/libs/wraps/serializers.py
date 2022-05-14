from rest_framework import serializers
from user.models import User, Metal


class EmptySerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class APIModelSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        self.Meta.model.before_create(validated_data)
        instance = super().create(validated_data)
        self.Meta.model.after_create(validated_data)
        return instance

    def update(self, instance, validated_data):
        self.Meta.model.before_update(instance, validated_data)
        instance = super().update(instance, validated_data)
        self.Meta.model.after_update(instance, validated_data)
        return instance


class MetalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metal
        fields = [
            "id",
            "description"
        ]


class UserSerializer(serializers.ModelSerializer):
    metal = MetalSerializer()

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
        ]


class OtherUserSerializer(serializers.ModelSerializer):
    metal = MetalSerializer()
    followed = serializers.SerializerMethodField()

    def get_followed(self, instance: User):
        return self.context["user"].my_follow.filter(followed=instance).exists()

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
            "up_num",
            "attention_num",
            "fans_num",
            "followed"
        ]


__all__ = [
    "EmptySerializer",
    "APIModelSerializer",
    "serializers",
    "UserSerializer",
    "OtherUserSerializer",
]
