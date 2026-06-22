from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.users.views import ModulesViewSet

router = DefaultRouter()
router.register("", ModulesViewSet, basename="modules")

urlpatterns = [path("", include(router.urls))]
