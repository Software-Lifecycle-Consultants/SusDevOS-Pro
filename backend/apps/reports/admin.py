from django.contrib import admin

from .models import ReportJobs


@admin.register(ReportJobs)
class ReportJobsAdmin(admin.ModelAdmin):
    list_display = ("ReportJobId", "EntityId", "ReportType", "Format", "JobStatus", "QueuedAt")
    list_filter = ("ReportType", "Format", "JobStatus")
    raw_id_fields = ("EntityId", "RequestedBy")
    readonly_fields = ("QueuedAt", "StartedAt", "CompletedAt", "CeleryTaskId", "S3Key", "FileSizeBytes")
