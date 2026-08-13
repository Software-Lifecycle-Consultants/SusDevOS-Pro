from django.contrib import admin

from .models import (
    LandParcelContacts,
    LandParcelDocuments,
    LandParcelEcosystems,
    LandParcelEntities,
    LandParcelImages,
    LandParcelLocations,
    LandParcels,
    LandParcelTags,
)


@admin.register(LandParcels)
class LandParcelsAdmin(admin.ModelAdmin):
    list_display = ("LandParcelId", "ParcelName", "EntityId", "AreaHectares", "LandUseType", "Status")
    list_filter = ("LandUseType", "Status")
    search_fields = ("ParcelName", "ParcelReference")
    raw_id_fields = ("EntityId",)

admin.site.register(LandParcelTags)
admin.site.register(LandParcelEcosystems)
admin.site.register(LandParcelContacts)
admin.site.register(LandParcelDocuments)
admin.site.register(LandParcelImages)
admin.site.register(LandParcelEntities)
admin.site.register(LandParcelLocations)
