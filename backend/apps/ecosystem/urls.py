from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EcosystemViewSet, SpeciesViewSet

router = DefaultRouter()
router.register("ecosystems", EcosystemViewSet, basename="ecosystems")
router.register("species",    SpeciesViewSet,   basename="species")
urlpatterns = [path("", include(router.urls))]
