"""
Report generation and housekeeping tasks.
"""
import logging

from django.utils.timezone import now

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="tasks.reports.generate_report",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    time_limit=300,  # 5 min hard limit
)
def generate_report(self, report_job_id: int):
    """
    Generate a report asynchronously.

    Steps:
      1. Mark job as Processing.
      2. Gather data for the report type.
      3. Render to PDF/CSV/JSON.
      4. Upload to S3.
      5. Mark job Complete with S3Key + FileSizeBytes.
      6. Send notification to requesting user.

    On failure: mark job Failed with ErrorMessage.
    """
    from apps.reports.models import ReportJobs

    try:
        job = ReportJobs.objects.get(ReportJobId=report_job_id)
    except ReportJobs.DoesNotExist:
        logger.error("ReportJob %s not found", report_job_id)
        return

    try:
        job.JobStatus = 2  # Processing
        job.StartedAt = now()
        job.save(update_fields=["JobStatus", "StartedAt"])

        result_key, file_size = _render_report(job)

        job.JobStatus = 3  # Complete
        job.S3Key = result_key
        job.FileSizeBytes = file_size
        job.CompletedAt = now()
        job.save(update_fields=["JobStatus", "S3Key", "FileSizeBytes", "CompletedAt"])

        _notify_complete(job)
        logger.info("Report %s generated: %s (%d bytes)", report_job_id, result_key, file_size)

    except Exception as exc:
        logger.exception("Report %s failed: %s", report_job_id, exc)
        try:
            job.JobStatus = 4  # Failed
            job.ErrorMessage = str(exc)[:500]
            job.CompletedAt = now()
            job.save(update_fields=["JobStatus", "ErrorMessage", "CompletedAt"])
            _notify_failed(job, str(exc))
        except Exception:
            pass
        raise self.retry(exc=exc)


def _render_report(job):
    """
    Gather data for the report type and render it to the requested format
    (JSON / CSV / PDF). Returns (s3_key, file_size_bytes).
    """
    import uuid

    from apps.reports.renderers import build_report_data, render

    data = build_report_data(job)
    content = render(data, job.Format)

    key = f"node-1/{job.EntityId_id}/reports/{uuid.uuid4()}.{job.Format}"
    _upload_to_storage(key, content, job.Format)
    return key, len(content)


def _upload_to_storage(key: str, content: bytes, fmt: str):
    """Upload to S3 (production) or write to /tmp (development)."""
    from django.conf import settings
    if getattr(settings, "DEFAULT_FILE_STORAGE", "").endswith("S3Boto3Storage"):
        import boto3
        s3 = boto3.client(
            "s3",
            endpoint_url=getattr(settings, "AWS_S3_ENDPOINT_URL", None),
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        content_types = {"pdf": "application/pdf", "csv": "text/csv", "json": "application/json"}
        s3.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
            Body=content,
            ContentType=content_types.get(fmt, "application/octet-stream"),
        )
    else:
        # Dev: write to /tmp
        import os
        import tempfile
        tmp_path = os.path.join(tempfile.gettempdir(), key.replace("/", "_"))
        with open(tmp_path, "wb") as f:
            f.write(content)


def _notify_complete(job):
    """Send in-app notification to the user who requested the report."""
    if not job.RequestedBy_id:
        return
    try:
        from apps.notifications.models import Notifications
        Notifications.objects.create(
            UserId_id=job.RequestedBy_id,
            EntityId_id=job.EntityId_id,
            Type="report_ready",
            Title="Your report is ready",
            Body=f"Your {job.ReportType} report ({job.Format.upper()}) has been generated.",
            RelatedModule="reports",
            RelatedRecordId=job.ReportJobId,
        )
    except Exception as exc:
        logger.warning("Failed to send report_ready notification: %s", exc)


def _notify_failed(job, reason: str):
    if not job.RequestedBy_id:
        return
    try:
        from apps.notifications.models import Notifications
        Notifications.objects.create(
            UserId_id=job.RequestedBy_id,
            EntityId_id=job.EntityId_id,
            Type="report_failed",
            Title="Report generation failed",
            Body=f"Your {job.ReportType} report could not be generated: {reason[:200]}",
            RelatedModule="reports",
            RelatedRecordId=job.ReportJobId,
        )
    except Exception as exc:
        logger.warning("Failed to send report_failed notification: %s", exc)


@shared_task(name="tasks.reports.purge_expired_reports")
def purge_expired_reports():
    """Delete ReportJob rows and their S3 files past their PurgeAfter date."""
    from apps.reports.models import ReportJobs

    expired = ReportJobs.objects.filter(PurgeAfter__lt=now())
    s3_keys = list(expired.exclude(S3Key__isnull=True).values_list("S3Key", flat=True))

    if s3_keys:
        _delete_s3_objects(s3_keys)

    deleted, _ = expired.delete()
    logger.info("purge_expired_reports: %d jobs deleted, %d S3 objects removed",
                deleted, len(s3_keys))
    return {"deleted": deleted, "s3_deleted": len(s3_keys)}


def _delete_s3_objects(keys: list[str]):
    from django.conf import settings
    if not getattr(settings, "DEFAULT_FILE_STORAGE", "").endswith("S3Boto3Storage"):
        return
    try:
        import boto3
        s3 = boto3.client(
            "s3",
            endpoint_url=getattr(settings, "AWS_S3_ENDPOINT_URL", None),
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        for i in range(0, len(keys), 1000):  # S3 delete_objects max 1000
            s3.delete_objects(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Delete={"Objects": [{"Key": k} for k in keys[i:i+1000]]},
            )
    except Exception as exc:
        logger.error("S3 bulk delete failed: %s", exc)
