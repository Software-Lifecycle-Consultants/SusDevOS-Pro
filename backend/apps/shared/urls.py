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


urlpatterns = [
    path("files/presign/", PresignedUploadView.as_view(), name="files-presign"),
]
