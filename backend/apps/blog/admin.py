from django.contrib import admin

from .models import Blogs


@admin.register(Blogs)
class BlogsAdmin(admin.ModelAdmin):
    list_display = ("BlogId", "Title", "EntityId", "BlogStatus", "PublishedAt", "Status")
    list_filter = ("BlogStatus", "Status")
    search_fields = ("Title", "Slug")
    prepopulated_fields = {"Slug": ("Title",)}
    raw_id_fields = ("EntityId", "AuthorId")
    readonly_fields = ("PublishedAt",)
