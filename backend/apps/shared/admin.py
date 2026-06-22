from django.contrib import admin

from .models import (
    Contacts,
    DocumentTags,
    Documents,
    EntityApiKeys,
    ImageTags,
    Images,
    Locations,
    Tags,
)


@admin.register(Locations)
class LocationsAdmin(admin.ModelAdmin):
    list_display = ("LocationId", "Title", "City", "Country", "Status")
    list_filter = ("Country", "Status")
    search_fields = ("Title", "City", "Country")


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ("TagId", "TagName", "EntityId", "Status")
    list_filter = ("Status",)
    search_fields = ("TagName",)
    readonly_fields = ("TagNameNormalized",)


@admin.register(Contacts)
class ContactsAdmin(admin.ModelAdmin):
    list_display = ("ContactId", "Name", "Email", "EntityId", "ModuleKey", "Status")
    list_filter = ("ModuleKey", "Status")
    search_fields = ("Name", "Email")


@admin.register(Documents)
class DocumentsAdmin(admin.ModelAdmin):
    list_display = ("DocumentId", "DocTitle", "EntityId", "ModuleKey", "DocType", "Status")
    list_filter = ("ModuleKey", "Status")
    search_fields = ("DocTitle",)


@admin.register(Images)
class ImagesAdmin(admin.ModelAdmin):
    list_display = ("ImageId", "AltText", "EntityId", "ModuleKey", "IsCover", "Status")
    list_filter = ("ModuleKey", "IsCover", "Status")


@admin.register(EntityApiKeys)
class EntityApiKeysAdmin(admin.ModelAdmin):
    list_display = ("ApiKeyId", "KeyPrefix", "EntityId", "ExpiryDate", "Status")
    list_filter = ("Status",)
    readonly_fields = ("HashedApiKey",)


admin.site.register(DocumentTags)
admin.site.register(ImageTags)
