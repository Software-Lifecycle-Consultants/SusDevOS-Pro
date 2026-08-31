"""Notifications app models. Ref: reference migration 0014_notifications."""
from django.db import models

NOTIFICATION_TYPE_CHOICES = [
    ("user_created", "New User Created"),
    ("emissions_submitted", "Emissions Record Submitted"),
    ("emissions_verified", "Emissions Record Verified"),
    ("emissions_unlocked", "Verified Record Unlocked"),
    ("system_error", "System Error"),
    ("access_denied", "Access Denied Attempt"),
    ("entity_created", "New Entity Created"),
    ("password_reset", "Password Reset Requested"),
    ("report_ready", "Report Generation Complete"),
    ("report_failed", "Report Generation Failed"),
]


class Notifications(models.Model):
    NotificationId = models.AutoField(primary_key=True)
    UserId = models.ForeignKey("users.Users", on_delete=models.CASCADE, related_name="notifications")
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.CASCADE, related_name="notifications")
    Type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    Title = models.CharField(max_length=200)
    Body = models.TextField()
    RelatedModule = models.CharField(max_length=50, blank=True)
    RelatedRecordId = models.IntegerField(null=True, blank=True)
    IsRead = models.BooleanField(default=False)
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        indexes = [
            models.Index(fields=["UserId", "IsRead", "CreatedAt"], name="idx_notif_user_unread"),
            models.Index(fields=["EntityId"], name="idx_notif_entity"),
        ]

    def __str__(self):
        return f"{self.Type} → {self.UserId_id}"
