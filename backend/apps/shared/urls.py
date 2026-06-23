"""Shared resource endpoints: file pre-signed URL generation."""
from django.urls import path
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class PresignedUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Returns a pre-signed S3 PUT URL for direct client-side upload.
        Body: { "filename": "report.pdf", "module_key": "projects", "record_id": 1 }
        """
        import uuid
        from django.conf import settings
        filename = request.data.get("filename", "file")
        module_key = request.data.get("module_key", "shared")
        record_id = request.data.get("record_id", "0")
        entity_id = getattr(request, "entity_id", "0")
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
        key = f"node-1/{entity_id}/{module_key}/{record_id}/{uuid.uuid4()}.{ext}"

        try:
            import boto3
            s3 = boto3.client(
                "s3",
                endpoint_url=getattr(settings, "AWS_S3_ENDPOINT_URL", None),
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            url = s3.generate_presigned_url(
                "put_object",
                Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
                ExpiresIn=3600,
            )
            return Response({"upload_url": url, "s3_key": key, "expires_in_seconds": 3600})
        except Exception:
            return Response({"s3_key": key,
                             "detail": "Pre-signed URL unavailable in dev — use s3_key directly."})


class AuditLogView(APIView):
    """
    GET /api/shared/audit-log/
    Returns the entity's audit log entries, newest first.
    Admin and SuperAdmin only — enforced by IsEntityAdmin permission.
    Supports ?action=, ?table=, ?days= query params.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.shared.models import AuditLog
        from apps.shared.permissions import IsEntityAdmin

        # Enforce admin-only access
        if not (getattr(request.user, "IsSuperAdmin", False) or
                IsEntityAdmin().has_permission(request, self)):
            return Response({"detail": "Admin access required."}, status=403)

        entity_id = getattr(request, "entity_id", None)
        if not entity_id and not getattr(request.user, "IsSuperAdmin", False):
            return Response({"results": []})

        qs = AuditLog.objects.select_related("ChangedBy")
        if not getattr(request.user, "IsSuperAdmin", False):
            qs = qs.filter(EntityId_id=entity_id)

        # Filters
        if request.query_params.get("action"):
            qs = qs.filter(Action=request.query_params["action"])
        if request.query_params.get("table"):
            qs = qs.filter(TableName=request.query_params["table"])
        if request.query_params.get("days"):
            from django.utils import timezone
            from datetime import timedelta
            since = timezone.now() - timedelta(days=int(request.query_params["days"]))
            qs = qs.filter(ChangedOn__gte=since)

        qs = qs.order_by("-ChangedOn")[:500]

        data = [
            {
                "LogId":             entry.LogId,
                "Action":            entry.Action,
                "TableName":         entry.TableName,
                "RecordId":          entry.RecordId,
                "Description":       entry.Description,
                "ChangedByUsername": entry.ChangedByUsername or (
                    entry.ChangedBy.username if entry.ChangedBy else "system"
                ),
                "ChangedOn":         entry.ChangedOn,
                "RetentionTier":     entry.RetentionTier,
            }
            for entry in qs
        ]
        return Response({"results": data, "count": len(data)})


urlpatterns = [
    path("files/presign/", PresignedUploadView.as_view(), name="files-presign"),
    path("audit-log/",     AuditLogView.as_view(),        name="audit-log"),
]
