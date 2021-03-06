from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import *

router = SimpleRouter()
router.register("dynamic", DynamicView, "")
router.register("reply", ReplyView, "")
router.register("like", LikeView, "")
router.register("at", AtView, "")
router.register("system", SystemView, "")
router.register("private", PrivateView, "")
router.register("private_detail", PrivateDetailView, "")
router.register("", MessageSettingView, "")

urlpatterns = [
    path("", include(router.urls))
]
