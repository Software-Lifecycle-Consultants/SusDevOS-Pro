from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.shared.views import EntityScopeInitialMixin

from .models import ReportJobs
from .serializers import ReportJobCreateSerializer, ReportJobSerializer


class ReportJobsViewSet(EntityScopeInitialMixin, ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        qs = ReportJobs.objects.all()
        if not getattr(user, "IsSuperAdmin", False):
            entity_id = getattr(self.request, "entity_id", None)
            qs = qs.filter(EntityId_id=entity_id) if entity_id else qs.none()
        return qs.order_by("-QueuedAt")

    def get_serializer_class(self):
        return ReportJobCreateSerializer if self.action == "create" else ReportJobSerializer

    def _check_export_gate(self):
        """CSV/JSON export is a Starter+ feature (report_csv_json_export,
        spec/pricing.md); PDF (watermarked on Free) is available to everyone, so
        the branding tier is applied at render time, not blocked here. Enforce
        the export gate server-side — frontend hiding does not count (CLAUDE.md
        rule #6)."""
        fmt = str(self.request.data.get("Format", "")).lower()
        if fmt not in ("csv", "json"):
            return
        if getattr(self.request.user, "IsSuperAdmin", False):  # SUPERADMIN_BYPASS
            return
        from apps.billing.mixins import FeatureGatedException
        from apps.billing.services import get_upgrade_message, is_feature_enabled

        entity_id = getattr(self.request, "entity_id", None)
        if not (entity_id and is_feature_enabled(entity_id=entity_id, feature_key="report_csv_json_export")):
            raise FeatureGatedException(
                feature_key="report_csv_json_export",
                message=get_upgrade_message(feature_key="report_csv_json_export"),
            )

    def perform_create(self, serializer):
        self._check_export_gate()
        entity_id = getattr(self.request, "entity_id", None)
        job = serializer.save(
            EntityId_id=entity_id,
            RequestedBy=self.request.user,
        )
        self._queue_report(job)

    def _queue_report(self, job):
        """Queue the Celery report task. Falls back gracefully if Celery unavailable."""
        try:
            from tasks.reports import generate_report
            result = generate_report.delay(job.ReportJobId)
            job.CeleryTaskId = result.id
            job.save(update_fields=["CeleryTaskId"])
        except Exception:
            # Celery not running in dev — job stays Queued, can be run manually
            pass

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        job = self.get_object()
        if job.JobStatus != 3:
            return Response(
                {"code": "not_ready", "detail": "Report is not yet complete."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not job.S3Key:
            return Response(
                {"code": "no_file", "detail": "No file available for this report."},
                status=status.HTTP_404_NOT_FOUND,
            )
        # In production: generate a pre-signed S3 URL (24h expiry)
        # In development: return the S3 key path for manual retrieval
        try:
            from django.conf import settings as dj_settings

            import boto3
            s3 = boto3.client(
                "s3",
                endpoint_url=getattr(dj_settings, "AWS_S3_ENDPOINT_URL", None),
                aws_access_key_id=dj_settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=dj_settings.AWS_SECRET_ACCESS_KEY,
            )
            url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": dj_settings.AWS_STORAGE_BUCKET_NAME, "Key": job.S3Key},
                ExpiresIn=86400,  # 24 hours
            )
            return Response({"download_url": url, "expires_in_seconds": 86400})
        except Exception:
            return Response({"s3_key": job.S3Key,
                             "detail": "Pre-signed URL generation unavailable in dev."})
