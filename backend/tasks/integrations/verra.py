"""
Verra VCS registry sync — daily 03:00 UTC.

Downloads the Verra issuance CSV, validates pending EmissionsOffsets
against the registry, and updates RegistryValidationStatus.
"""
import codecs
import csv
import logging

from django.conf import settings
from django.utils.timezone import now

import requests

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="tasks.integrations.sync_verra_registry",
    bind=True,
    max_retries=2,
    default_retry_delay=1800,
)
def sync_verra_registry(self):
    """
    Download Verra CSV, cache serial numbers, then re-validate pending offsets.
    The Verra CSV is large (~500 MB); we stream it and look for exact serial matches.
    """
    from apps.emissions.models import EmissionsOffsets

    csv_url = getattr(settings, "VERRA_CSV_URL", "")
    if not csv_url:
        logger.warning("VERRA_CSV_URL not set — skipping Verra sync")
        return {"skipped": "no URL configured"}

    # Build a set of known-valid serial numbers from the CSV
    valid_serials: set[str] = set()
    retired_serials: dict[str, str] = {}  # serial → beneficiary

    try:
        resp = requests.get(csv_url, timeout=120, stream=True)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise self.retry(exc=exc)

    reader = csv.DictReader(codecs.iterdecode(resp.iter_lines(), "utf-8"))
    for row in reader:
        serial = (row.get("Serial Number") or "").strip()
        if not serial:
            continue
        valid_serials.add(serial)
        beneficiary = (row.get("Retirement Beneficiary") or "").strip()
        if beneficiary:
            retired_serials[serial] = beneficiary

    logger.info("Verra CSV: %d valid serial numbers loaded", len(valid_serials))

    # A truncated/empty download parses to zero (or a suspiciously tiny number of)
    # serials AFTER raise_for_status has already passed. Validating against it
    # would flip every genuinely-valid credit to "invalid", and because the
    # requery below only reconsiders pending/unverified rows, that corruption is
    # sticky. Abort rather than mass-invalidate on an empty registry.
    if not valid_serials:
        logger.error(
            "Verra CSV yielded 0 serial numbers — aborting to avoid mass-invalidation"
        )
        return {"skipped": "empty or unparseable CSV", "validated": 0, "invalidated": 0}

    # Validate pending offsets. Only touch credits flagged as Verra (or unflagged
    # legacy rows) — never mark a Gold Standard credit invalid against the VCS list.
    from django.db.models import Q
    pending = EmissionsOffsets.objects.filter(
        Q(CreditRegistry="verra") | Q(CreditRegistry__isnull=True),
        RegistryValidationStatus__in=["pending", "unverified"],
        CreditSerialNumber__isnull=False,
    )
    validated = 0
    invalidated = 0

    for offset in pending:
        serial = (offset.CreditSerialNumber or "").strip()
        if serial in valid_serials:
            offset.RegistryValidationStatus = "valid"
            offset.RegistryRetirementBeneficiary = retired_serials.get(serial)
            offset.RegistryValidatedAt = now()
            offset.save(update_fields=[
                "RegistryValidationStatus", "RegistryRetirementBeneficiary",
                "RegistryValidatedAt",
            ])
            validated += 1
        else:
            offset.RegistryValidationStatus = "invalid"
            offset.RegistryValidatedAt = now()
            offset.save(update_fields=["RegistryValidationStatus", "RegistryValidatedAt"])
            invalidated += 1

    logger.info(
        "Verra validation: %d valid, %d invalid out of %d pending",
        validated, invalidated, pending.count(),
    )
    return {"validated": validated, "invalidated": invalidated}
