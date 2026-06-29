"""
Gold Standard registry validation — daily 03:30 UTC.

Unlike Verra (bulk CSV issuance table), Gold Standard exposes a public
per-project registry, so we validate each pending Gold-Standard-flagged offset
individually by project/credit identifier and populate the Registry* fields.

Safe when unconfigured or when the registry is unreachable: offsets are left
"pending" (never wrongly marked "invalid" on a network error).
"""
import logging

import requests
from celery import shared_task
from django.conf import settings
from django.utils.timezone import now

logger = logging.getLogger(__name__)

TIMEOUT = 15
# Public registry base; overridable for testing / API changes.
DEFAULT_BASE = "https://registry.goldstandard.org/projects/details"


def _base_url():
    return getattr(settings, "GOLD_STANDARD_API_URL", "") or DEFAULT_BASE


def _validate_one(offset) -> str:
    """
    Validate a single offset against the Gold Standard registry.
    Returns the new RegistryValidationStatus ("valid"/"invalid"/"pending").
    "pending" means "could not determine" (network error) — left for retry.
    """
    project_ref = (offset.CreditSerialNumber or offset.CertificateNumber or "").strip()
    if not project_ref:
        return "invalid"  # nothing to look up

    try:
        resp = requests.get(f"{_base_url()}/{requests.utils.quote(project_ref)}", timeout=TIMEOUT)
    except requests.RequestException as exc:
        logger.warning("Gold Standard lookup failed for %s: %s", project_ref, exc)
        return "pending"

    if resp.status_code == 404:
        return "invalid"
    if resp.status_code >= 400:
        return "pending"  # transient/server-side — retry next run

    try:
        data = resp.json()
    except ValueError:
        # Some registry endpoints return HTML; a 200 means the project page exists.
        data = {}

    offset.RegistryProjectName = data.get("name") or data.get("project_name") or offset.RegistryProjectName
    offset.RegistryProjectType = data.get("type") or data.get("project_type") or offset.RegistryProjectType
    vintage = data.get("vintage") or data.get("vintage_year")
    if vintage:
        try:
            offset.RegistryVintageYear = int(str(vintage)[:4])
        except (ValueError, TypeError):
            pass
    return "valid"


@shared_task(
    name="tasks.integrations.sync_gold_standard_registry",
    bind=True,
    max_retries=2,
    default_retry_delay=1800,
)
def sync_gold_standard_registry(self):
    """Re-validate pending Gold-Standard-flagged offsets against the public registry."""
    from apps.emissions.models import EmissionsOffsets

    pending = EmissionsOffsets.objects.filter(
        CreditRegistry="gold_standard",
        RegistryValidationStatus__in=["pending", "unverified"],
    )

    validated = invalidated = deferred = 0
    for offset in pending:
        status = _validate_one(offset)
        if status == "pending":
            deferred += 1
            continue
        offset.RegistryValidationStatus = status
        offset.RegistryValidatedAt = now()
        offset.save(update_fields=[
            "RegistryValidationStatus", "RegistryValidatedAt",
            "RegistryProjectName", "RegistryProjectType", "RegistryVintageYear",
        ])
        validated += status == "valid"
        invalidated += status == "invalid"

    logger.info(
        "Gold Standard validation: %d valid, %d invalid, %d deferred",
        validated, invalidated, deferred,
    )
    return {"validated": validated, "invalidated": invalidated, "deferred": deferred}
