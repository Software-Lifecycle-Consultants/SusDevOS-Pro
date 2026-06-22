from django.contrib import admin
from .models import Ecosystem, EcosystemTags, Species, SpeciesTags, SpeciesLandParcels

@admin.register(Ecosystem)
class EcosystemAdmin(admin.ModelAdmin):
    list_display = ("EcosystemId", "EcosystemName", "EcosystemType", "EntityId", "Status")
    list_filter = ("EcosystemType", "Status")
    search_fields = ("EcosystemName",)

@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ("SpeciesId", "CommonName", "ScientificName", "IUCNStatus", "EntityId", "Status")
    list_filter = ("IUCNStatus", "Status")
    search_fields = ("CommonName", "ScientificName")

admin.site.register(EcosystemTags)
admin.site.register(SpeciesTags)
admin.site.register(SpeciesLandParcels)
