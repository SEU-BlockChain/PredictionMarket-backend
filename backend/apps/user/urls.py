from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import *

router = SimpleRouter()
router.register("", RegisterView, "register")
router.register("", LoginView, "login")
router.register("", UserInfoView, "user_info")
router.register("reply", ReplyView, "bbs_reply")

urlpatterns = [
    path("", include(router.urls))
]
