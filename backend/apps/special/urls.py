from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import *

router = SimpleRouter()
router.register("self", MyColumnView, "")
router.register("tag", TagView, "")
router.register("column", ColumnView, "")
router.register("^column/(?P<column_id>[0-9]+)/comment", CommentView, "")
router.register("^column/(?P<column_id>[0-9]+)/comment/(?P<parent_id>[0-9]+)/children_comment", ChildrenCommentView,
                "")
urlpatterns = [
    path("", include(router.urls))
]
