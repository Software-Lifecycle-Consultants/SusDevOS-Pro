from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import LandParcelsViewSet

router = DefaultRouter()
router.register("", LandParcelsViewSet, basename="land-parcels")
urlpatterns = [path("", include(router.urls))]
