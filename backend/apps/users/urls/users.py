from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.users.views import MePasswordView, MeView, UsersViewSet

router = DefaultRouter()
router.register("", UsersViewSet, basename="users")

urlpatterns = [
    path("me/",          MeView.as_view(),         name="users-me"),
    path("me/password/", MePasswordView.as_view(),  name="users-me-password"),
    path("",             include(router.urls)),
]
