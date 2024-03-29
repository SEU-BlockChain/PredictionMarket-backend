from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import *

router = SimpleRouter()
router.register("article", ArticleView, "")
router.register("draft", DraftView, "")
router.register("category", CategoryView, "")
router.register("collection", CollectionView, "")
router.register("collection/(?P<collection_id>[0-9]+)/info", CollectionInfoView, "")
router.register("collection/(?P<collection_id>[0-9]+)/article", CollectionArticleView, "")
router.register("^article/(?P<article_id>[0-9]+)/comment", CommentView, "")
router.register("^article/(?P<article_id>[0-9]+)/comment/(?P<parent_id>[0-9]+)/children_comment", ChildrenCommentView,
                "")

urlpatterns = [
    path("", include(router.urls))
]
