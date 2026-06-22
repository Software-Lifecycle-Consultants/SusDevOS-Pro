from django.contrib import admin
from .models import Notifications

@admin.register(Notifications)
class NotificationsAdmin(admin.ModelAdmin):
    list_display = ("NotificationId", "UserId", "EntityId", "Type", "Title", "IsRead", "CreatedAt")
    list_filter = ("Type", "IsRead")
    search_fields = ("Title",)
    raw_id_fields = ("UserId", "EntityId")
