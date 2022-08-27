from django.urls import path, include

urlpatterns = [
    path("common/", include("common.urls")),
    path("user/", include("user.urls")),
    path("bbs/", include("bbs.urls")),
    path("special/", include("special.urls")),
    path("task/", include("task.urls")),
    path("other/", include("other.urls")),
    path("information/", include("information.urls")),
    path("message/", include("message.urls")),
    path("issue/", include("issue.urls")),
    path("vote/", include("vote.urls")),
]
