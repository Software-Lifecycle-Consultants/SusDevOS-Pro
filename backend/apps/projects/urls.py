from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import DevelopmentProjectsViewSet

router = DefaultRouter()
router.register("", DevelopmentProjectsViewSet, basename="projects")
urlpatterns = [path("", include(router.urls))]
