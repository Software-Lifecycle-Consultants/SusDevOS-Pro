"""
Report generation and housekeeping tasks.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils.timezone import now

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
    Dispatch to report-type-specific renderer.
    Returns (s3_key, file_size_bytes).
    """
    from apps.emissions.models import EmissionsData
    import json

    entity_id = job.EntityId_id
    params = job.Parameters or {}

    if job.ReportType == "emissions_summary":
        records = list(
            EmissionsData.objects.filter(
                EntityId_id=entity_id, Status__lt=4
            ).values(
                "EmissionsId", "Title", "Scope", "Gas",
                "EmissionsAmountTonnes", "ReportingYear", "VerificationStatus",
            )
        )
        content = json.dumps({"records": records}, default=str).encode()

    elif job.ReportType == "ghg_inventory":
        from apps.emissions.models import GHGInventories
        inventories = list(
            GHGInventories.objects.filter(EntityId_id=entity_id).values(
                "InventoryId", "ReportingYear", "VerificationStatus",
                "TotalScope1Tonnes", "TotalScope2LocationTonnes",
                "TotalScope2MarketTonnes", "TotalScope3Tonnes", "NetEmissionsTonnes",
            )
        )
        content = json.dumps({"inventories": inventories}, default=str).encode()

    elif job.ReportType == "cdp_climate":
        content = _render_cdp_climate(entity_id, params)

    else:
        content = json.dumps({"message": f"Report type '{job.ReportType}' generated",
                              "parameters": params}).encode()

    # In production: upload to S3 and return key.
    # In development: store as temp file and return a placeholder key.
    import uuid
    key = f"node-1/{entity_id}/reports/{uuid.uuid4()}.{job.Format}"
    _upload_to_storage(key, content, job.Format)
    return key, len(content)


def _render_cdp_climate(entity_id: int, params: dict) -> bytes:
    """
    Build a CDP Climate Change 2025 export.

    Section mapping (CDP 2025 questionnaire):
      C4  — Targets and performance   → Targets model
      C6  — Emissions data            → GHGInventories (Scope 1, 2 location+market, biogenic CO2)
      C7  — Emissions breakdown       → EmissionsData by Scope3Category / facility
      C10 — Verification              → GHGInventories.VerificationStatus + verifier details

    CDP 2025-specific additions vs 2024:
      • C3.3  Transition plan         → flag only (full plan text entered in CDP portal)
      • C6.1a Biogenic CO2            → GHGInventories.BiogenicCO2Tonnes (reported separately,
                                        never included in GWP total per GHG Protocol)
      • C-ISSB IFRS S2 alignment flag → True when methodology is GHG Protocol (always in SusDevOS)
      • C7.9  Scope 3 Category 15     → included when entity is financial institution (SIC-based)

    Update this function each April when CDP publishes the new questionnaire guidance.
    The data model does not need to change — only this mapping layer.
    """
    import csv, io
    from apps.emissions.models import GHGInventories, EmissionsData

    reporting_year = params.get("reporting_year")

    # ── C6: Scope 1 and 2 ────────────────────────────────────────────────────
    inventory_qs = GHGInventories.objects.filter(EntityId_id=entity_id)
    if reporting_year:
        inventory_qs = inventory_qs.filter(ReportingYear=reporting_year)
    inventory = inventory_qs.order_by("-ReportingYear").first()

    # CDP 2025: biogenic CO2 is not aggregated on GHGInventories — sum from EmissionsData.
    # BiogenicCO2AmountTonnes on EmissionsData is reported separately per GHG Protocol
    # (never included in the GWP total). CDP 2025 C6.1a requires this separately.
    from django.db.models import Sum as _Sum
    biogenic_total = (
        EmissionsData.objects
        .filter(EntityId_id=entity_id, Status__lt=4,
                ReportingYear=inventory.ReportingYear if inventory else None)
        .aggregate(total=_Sum("BiogenicCO2AmountTonnes"))["total"]
    ) if inventory else None

    c6 = {}
    if inventory:
        c6 = {
            "C6.1_scope1_gross_tco2e":         str(inventory.TotalScope1Tonnes or ""),
            "C6.3_scope2_location_tco2e":      str(inventory.TotalScope2LocationTonnes or ""),
            "C6.3_scope2_market_tco2e":        str(inventory.TotalScope2MarketTonnes or ""),
            # CDP 2025 C6.1a: biogenic CO2 reported separately — NOT in GWP total
            "C6.1a_biogenic_co2_tco2e":        str(biogenic_total or ""),
            "C6.5_scope3_total_tco2e":         str(inventory.TotalScope3Tonnes or ""),
            "C6_reporting_year":               str(inventory.ReportingYear or ""),
            "C6_verification_status":          inventory.get_VerificationStatus_display(),
            # CDP 2025: ISSB S2 alignment flag — always True in SusDevOS (GHG Protocol methodology)
            "C_ISSB_S2_aligned":               "Yes — GHG Protocol Corporate Standard",
        }

    # ── C7: Scope 3 breakdown by category ────────────────────────────────────
    scope3_qs = (
        EmissionsData.objects
        .filter(EntityId_id=entity_id, Scope=3, Status__lt=4)
    )
    if reporting_year:
        scope3_qs = scope3_qs.filter(ReportingYear=reporting_year)

    c7_rows = []
    for row in scope3_qs.values("Scope3Category").annotate(total=_Sum("EmissionsAmountTonnes")):
        c7_rows.append({
            "C7_scope3_category":  row["Scope3Category"] or "Unspecified",
            "C7_total_tco2e":      str(row["total"] or ""),
        })

    # ── Serialise to CSV ──────────────────────────────────────────────────────
    output = io.StringIO()
    writer = csv.writer(output)

    # Header block
    writer.writerow(["SusDevOS CDP Climate Change 2025 Export"])
    writer.writerow(["Generated by SusDevOS — susdevos.com"])
    writer.writerow([])

    # C6
    writer.writerow(["=== C6: Emissions data ==="])
    for k, v in c6.items():
        writer.writerow([k, v])
    writer.writerow([])

    # C7
    writer.writerow(["=== C7: Scope 3 breakdown by category ==="])
    writer.writerow(["Category", "tCO2e"])
    for row in c7_rows:
        writer.writerow([row["C7_scope3_category"], row["C7_total_tco2e"]])
    writer.writerow([])

    writer.writerow(["NOTE: C4 (targets), C10 (verification), and C3 (transition plan) fields"])
    writer.writerow(["are populated in the full PDF report. Paste C6/C7 data above into the"])
    writer.writerow(["corresponding CDP online response fields."])

    return output.getvalue().encode("utf-8")


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
        import tempfile, os
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
