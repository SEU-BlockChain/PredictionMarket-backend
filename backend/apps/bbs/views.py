from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from .models import *
from .serializers import *
from backend.libs import *


class ArticleView(APIModelViewSet):
    authentication_classes = [CommonJwtAuthentication]
    queryset = Articles.objects.filter(is_active=True)
    serializer_class = ArticleSerializer

    def get_queryset(self):
        order = self.request.query_params.get("order", "create_time")
        return self.queryset.order_by(order).all()


__all__ = [
    "ArticleView"
]
