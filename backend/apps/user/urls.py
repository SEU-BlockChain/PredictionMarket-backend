from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import *

router = SimpleRouter()
router.register("sign", SignView, "sign")
router.register("self", UserInfoView, "user_info")
router.register("info", OtherUserView, "")
router.register("follow", FollowView, "follow")
router.register("black_list", BlackListView, "black_list")

urlpatterns = [
    path("", include(router.urls))
]
