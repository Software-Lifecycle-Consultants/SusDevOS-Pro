from django.contrib import admin
from .models import (
    LandParcels, LandParcelTags, LandParcelEcosystems, LandParcelContacts,
    LandParcelDocuments, LandParcelImages, LandParcelEntities, LandParcelLocations,
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
