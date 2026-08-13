from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RestorationsViewSet, TreeRemovalsViewSet

router = DefaultRouter()
router.register("tree-removals", TreeRemovalsViewSet, basename="tree-removals")
router.register("restorations",  RestorationsViewSet, basename="restorations")
urlpatterns = [path("", include(router.urls))]
