from rest_framework import serializers
from .models import Notifications


class NotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = ("NotificationId", "Type", "Title", "Body",
                  "RelatedModule", "RelatedRecordId", "IsRead", "CreatedAt")
        read_only_fields = ("NotificationId", "Type", "Title", "Body",
                            "RelatedModule", "RelatedRecordId", "CreatedAt")
