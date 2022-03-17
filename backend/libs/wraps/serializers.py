from rest_framework import serializers


class EmptySerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


__all__ = [
    "EmptySerializer",
    "serializers",
]
