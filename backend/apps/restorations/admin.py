from django.contrib import admin
from .models import (
    TreeRemovals, TreeRemovalEcosystems, TreeRemovalTags, TreeRemovalContacts,
    TreeRemovalDocuments, TreeRemovalLandParcels, TreeRemovalEntities,
    TreeRemovalImages, TreeRemovalRemovedSpecies, TreeRemovalAffectedSpecies,
    Restorations, RestorationEcosystems, RestorationTags, RestorationDevelopmentProjects,
    RestorationEntities, RestorationSpecies, RestorationLandParcels,
    RestorationLocations, RestorationContacts, RestorationDocuments, RestorationImages,
)

@admin.register(TreeRemovals)
class TreeRemovalsAdmin(admin.ModelAdmin):
    list_display = ("TreeRemovalId", "EntityId", "ProjectId", "RemovalDate", "TotalTreesRemoved", "Status")
    list_filter = ("Status",)
    raw_id_fields = ("EntityId", "ProjectId")

@admin.register(Restorations)
class RestorationsAdmin(admin.ModelAdmin):
    list_display = ("RestorationId", "RestorationName", "EntityId", "StartDate", "TotalTreesPlanted", "Status")
    list_filter = ("Status",)
    search_fields = ("RestorationName", "RestorationReference")
    raw_id_fields = ("EntityId",)

for _model in [
    TreeRemovalEcosystems, TreeRemovalTags, TreeRemovalContacts, TreeRemovalDocuments,
    TreeRemovalLandParcels, TreeRemovalEntities, TreeRemovalImages,
    TreeRemovalRemovedSpecies, TreeRemovalAffectedSpecies,
    RestorationEcosystems, RestorationTags, RestorationDevelopmentProjects,
    RestorationEntities, RestorationSpecies, RestorationLandParcels,
    RestorationLocations, RestorationContacts, RestorationDocuments, RestorationImages,
]:
    admin.site.register(_model)
