"""
SBTi Companies Taking Action registry sync — monthly, 1st of month 02:00 UTC.

Downloads the SBTi CSV, matches against Entities by SBTiCompanyId (exact)
or EntityName (fuzzy, confidence >= 0.85), and updates Targets.SBTiStatus.
"""
import csv
import logging
from difflib import SequenceMatcher
from io import StringIO

import requests
from celery import shared_task
from django.conf import settings
from django.utils.timezone import now

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.85


@shared_task(
    name="tasks.integrations.sync_sbti_registry",
    bind=True,
    max_retries=2,
    default_retry_delay=1800,
)
def sync_sbti_registry(self):
    """Download SBTi CSV and update matching Targets.SBTiStatus."""
    from apps.entities.models import Entities
    from apps.emissions.models import Targets

    csv_url = getattr(settings, "SBTI_COMPANIES_CSV_URL", "")
    if not csv_url:
        logger.warning("SBTI_COMPANIES_CSV_URL not set — skipping SBTi sync")
        return {"skipped": "no URL configured"}

    try:
        resp = requests.get(csv_url, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise self.retry(exc=exc)

    reader = csv.DictReader(StringIO(resp.text))
    matched = 0
    review_queue = []

    for row in reader:
        sbti_id = (row.get("ID") or "").strip()
        name    = (row.get("Company Name") or "").strip()
        status  = (row.get("Target Status") or "").strip()
        if not name:
            continue

        # 1. Exact match by SBTiCompanyId
        entity = Entities.objects.filter(SBTiCompanyId=sbti_id).first() if sbti_id else None

        # 2. Fuzzy match by EntityName
        if not entity:
            entity, confidence = _fuzzy_match_entity(name)
            if entity and confidence < CONFIDENCE_THRESHOLD:
                review_queue.append({
                    "sbti_name":      name,
                    "matched_entity": entity.EntityId,
                    "confidence":     round(confidence, 3),
                })
                entity = None  # don't apply until manually reviewed

        if entity:
            Targets.objects.filter(EntityId=entity).update(
                SBTiStatus=status,
                SBTiLastSyncedAt=now(),
            )
            if sbti_id and not entity.SBTiCompanyId:
                entity.SBTiCompanyId = sbti_id
                entity.save(update_fields=["SBTiCompanyId"])
            matched += 1

    if review_queue:
        _create_review_notifications(review_queue)

    logger.info(
        "SBTi sync: %d entities matched, %d queued for review",
        matched, len(review_queue),
    )
    return {"matched": matched, "review_queue": len(review_queue)}


def _fuzzy_match_entity(name: str):
    """Return (entity, confidence) for best name match, or (None, 0)."""
    from apps.entities.models import Entities

    best_entity     = None
    best_confidence = 0.0

    for entity in Entities.objects.filter(Status__lt=4).only("EntityId", "EntityName"):
        confidence = SequenceMatcher(
            None, name.lower(), entity.EntityName.lower()
        ).ratio()
        if confidence > best_confidence:
            best_confidence = confidence
            best_entity = entity

    return best_entity, best_confidence


def _create_review_notifications(queue: list[dict]):
    """Notify SuperAdmins about SBTi matches that need manual review."""
    from apps.users.models import Users
    from apps.notifications.models import Notifications

    superadmins = Users.objects.filter(IsSuperAdmin=True, is_active=True)
    for sa in superadmins:
        if not sa.EntityId_id:
            continue
        body = f"{len(queue)} SBTi company matches need review:\n\n" + "\n".join(
            f"• '{r['sbti_name']}' → entity {r['matched_entity']} ({r['confidence']*100:.0f}% confidence)"
            for r in queue[:10]
        )
        Notifications.objects.create(
            UserId=sa,
            EntityId_id=sa.EntityId_id,
            Type="system_error",
            Title="SBTi matches require review",
            Body=body,
        )
