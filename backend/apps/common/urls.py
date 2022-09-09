from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import *

router = SimpleRouter()
router.register("", SMSCodeView, "")
router.register("image", ImageView, "")
router.register("recommend", RecommendView, "")
router.register("eth", FaucetView, "")
router.register("sticky", StickyView, "")
router.register("sign", SignView, "")

urlpatterns = [
    path("", include(router.urls))
]
