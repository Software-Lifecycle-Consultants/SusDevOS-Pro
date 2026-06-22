from django.contrib import admin

from .models import (
    Entities,
    EntityApiKeysIntermediary,
    EntityContacts,
    EntityDocuments,
    EntityLocations,
    EntityTags,
    RelatedEntities,
)


@admin.register(Entities)
class EntitiesAdmin(admin.ModelAdmin):
    list_display = ("EntityId", "EntityName", "EntityType", "Country", "Status")
    list_filter = ("EntityType", "Status", "Country")
    search_fields = ("EntityName", "RegistrationNumber", "CompaniesHouseNumber")
    readonly_fields = ("CreatedAt", "UpdatedAt")


@admin.register(RelatedEntities)
class RelatedEntitiesAdmin(admin.ModelAdmin):
    list_display = ("id", "ParentEntityId", "ChildEntityId", "RelationshipType")
    raw_id_fields = ("ParentEntityId", "ChildEntityId")


admin.site.register(EntityLocations)
admin.site.register(EntityContacts)
admin.site.register(EntityDocuments)
admin.site.register(EntityTags)
admin.site.register(EntityApiKeysIntermediary)
