from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import *

router = SimpleRouter()
router.register("^(?P<address>[0-9]+)/comment", IssueCommentView, "")
router.register("^(?P<address>[0-9]+)/comment/(?P<parent_id>[0-9]+)/children_comment", IssueChildrenCommentView, "")

urlpatterns = [
    path("", include(router.urls))
]
