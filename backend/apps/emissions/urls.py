from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    EmissionFactorSetsViewSet, EmissionFactorsViewSet,
    EmissionsDataViewSet, EmissionsOffsetsViewSet, GwpDatasetsViewSet,
    GHGInventoriesViewSet, TargetsViewSet,
)

router = DefaultRouter()
router.register("emissions",            EmissionsDataViewSet,     basename="emissions")
router.register("emissions-offsets",    EmissionsOffsetsViewSet,  basename="emissions-offsets")
router.register("gwp-datasets",         GwpDatasetsViewSet,       basename="gwp-datasets")
router.register("ghg-inventories",      GHGInventoriesViewSet,    basename="ghg-inventories")
router.register("targets",              TargetsViewSet,            basename="targets")
router.register("emission-factor-sets", EmissionFactorSetsViewSet, basename="emission-factor-sets")
router.register("emission-factors",     EmissionFactorsViewSet,    basename="emission-factors")
urlpatterns = [path("", include(router.urls))]
