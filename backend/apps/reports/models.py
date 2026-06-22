"""Reports app models. Ref: reference migration 0017_report_jobs."""
from datetime import timedelta

from django.db import models
from django.utils import timezone

REPORT_TYPE_CHOICES = [
    ("emissions_summary", "Project Emissions Summary"),
    ("ghg_inventory", "Entity GHG Inventory"),
    ("phase_progress", "Phase Progress vs Goals"),
    ("tree_log", "Tree Removal & Restoration Log"),
]

REPORT_FORMAT_CHOICES = [("pdf", "PDF"), ("csv", "CSV"), ("json", "JSON")]

REPORT_STATUS_CHOICES = [(1, "Queued"), (2, "Processing"), (3, "Complete"), (4, "Failed")]


class ReportJobs(models.Model):
    ReportJobId = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.PROTECT, related_name="report_jobs")
    RequestedBy = models.ForeignKey(
        "users.Users", on_delete=models.SET_NULL, null=True, related_name="report_jobs"
    )
    ReportType = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    Format = models.CharField(max_length=10, choices=REPORT_FORMAT_CHOICES)
    Parameters = models.JSONField(default=dict)
    JobStatus = models.PositiveSmallIntegerField(default=1, choices=REPORT_STATUS_CHOICES)
    CeleryTaskId = models.CharField(max_length=255, blank=True, null=True)
    S3Key = models.TextField(blank=True, null=True)
    FileSizeBytes = models.BigIntegerField(null=True, blank=True)
    ErrorMessage = models.TextField(blank=True, null=True)
    QueuedAt = models.DateTimeField(auto_now_add=True)
    StartedAt = models.DateTimeField(null=True, blank=True)
    CompletedAt = models.DateTimeField(null=True, blank=True)
    PurgeAfter = models.DateTimeField()

    class Meta:
        db_table = "report_jobs"
        ordering = ["-QueuedAt"]
        indexes = [
            models.Index(fields=["EntityId", "JobStatus"], name="idx_report_entity_status"),
            models.Index(fields=["PurgeAfter"], name="idx_report_purge"),
        ]

    def save(self, *args, **kwargs):
        if not self.PurgeAfter:
            self.PurgeAfter = timezone.now() + timedelta(days=90)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ReportType} ({self.get_JobStatus_display()})"
