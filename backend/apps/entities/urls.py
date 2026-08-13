from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EntitiesViewSet

router = DefaultRouter()
router.register("", EntitiesViewSet, basename="entities")

urlpatterns = [path("", include(router.urls))]
