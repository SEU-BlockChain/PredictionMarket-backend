from django.db import models


class APIModel(models.Model):
    def before_create(self, validated_data):
        pass

    def after_create(self, validated_data):
        pass

    def before_update(self, instance, validated_data):
        pass

    def after_update(self, instance, validated_data):
        pass

    class Meta:
        abstract = True


__all__ = [
    "APIModel",
    "models",
]
