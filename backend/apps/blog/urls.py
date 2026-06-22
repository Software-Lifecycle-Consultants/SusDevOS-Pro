from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import BlogsViewSet

router = DefaultRouter()
router.register("", BlogsViewSet, basename="blog")
urlpatterns = [path("", include(router.urls))]
