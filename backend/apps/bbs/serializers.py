from .models import *
from backend.libs import *


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Articles
        fields = "__all__"


__all__ = [
    "ArticleSerializer"
]
