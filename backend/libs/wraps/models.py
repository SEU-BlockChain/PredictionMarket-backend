from django.db import models


class APIModel(models.Model):

    def after_create(self, validated_data, serializer):
        pass

    def after_update(self, validated_data, serializer):
        pass

    class Meta:
        abstract = True
