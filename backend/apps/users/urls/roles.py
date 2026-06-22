from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.users.views import RolesViewSet

router = DefaultRouter()
router.register("", RolesViewSet, basename="roles")

urlpatterns = [path("", include(router.urls))]
