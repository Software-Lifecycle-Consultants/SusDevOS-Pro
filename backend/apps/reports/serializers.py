from rest_framework import serializers

from .models import ReportJobs


class ReportJobSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_JobStatus_display", read_only=True)

    class Meta:
        model = ReportJobs
        fields = ("ReportJobId", "ReportType", "Format", "Parameters",
                  "JobStatus", "status_label", "CeleryTaskId",
                  "FileSizeBytes", "ErrorMessage",
                  "QueuedAt", "StartedAt", "CompletedAt", "PurgeAfter")
        read_only_fields = ("ReportJobId", "JobStatus", "status_label", "CeleryTaskId",
                            "FileSizeBytes", "ErrorMessage",
                            "QueuedAt", "StartedAt", "CompletedAt", "PurgeAfter")


class ReportJobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportJobs
        fields = ("ReportType", "Format", "Parameters")
