"""
Climatiq emission-factor sync — weekly (Sunday 02:00 UTC).

Refreshes locally-cached Climatiq emission factors whose ExternalSyncedAt is
older than 7 days (per api_integrations.md §1 caching strategy). On-demand
single-factor lookup is also exposed via fetch_climatiq_factor() for the
emissions calculation fallback path.

Safe when unconfigured: if CLIMATIQ_API_KEY is unset the task logs and returns
a "skipped" result rather than raising — so the beat schedule never crashes.
"""
import logging
from datetime import timedelta
from decimal import Decimal

import requests
from celery import shared_task
from django.conf import settings
from django.db import models
from django.utils.timezone import now

logger = logging.getLogger(__name__)

CLIMATIQ_BASE = "https://api.climatiq.io/data/v1"
TIMEOUT = 10
STALE_AFTER = timedelta(days=7)


def _api_key():
    return getattr(settings, "CLIMATIQ_API_KEY", None)


def fetch_climatiq_factor(activity_id: str, region: str, year: int):
    """
    Look up one emission factor from Climatiq's search endpoint.
    Returns the parsed first result dict, or None if no match / not configured.
    Raises requests.HTTPError on a non-2xx response so callers can retry.
    """
    api_key = _api_key()
    if not api_key:
        logger.warning("CLIMATIQ_API_KEY not set — skipping Climatiq lookup for %s", activity_id)
        return None

    resp = requests.get(
        f"{CLIMATIQ_BASE}/search",
        params={"query": activity_id, "region": region, "year": year},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0] if results else None


def _get_climatiq_set():
    """Get-or-create the shared 'Climatiq Aggregated' EmissionFactorSets row."""
    from apps.emissions.models import EmissionFactorSets
    ef_set, _ = EmissionFactorSets.objects.get_or_create(
        SetName="Climatiq Aggregated",
        Publisher="Climatiq",
        defaults={"GeographicScope": "Global", "IsActive": True},
    )
    return ef_set


def lookup_or_fetch_factor(*, activity_id: str, region: str, year: int,
                           scope: int, gas: str = "CO2e"):
    """
    On-demand emission-factor resolution (api_integrations §1 fallback path).

    Returns a cached EmissionFactors row when a fresh (<7-day) one exists for
    (ClimatiqActivityId, CountryCode, ApplicableYear); otherwise fetches from
    Climatiq, upserts, and returns it. Returns None if unconfigured or no match.
    """
    from apps.emissions.models import EmissionFactors

    cached = EmissionFactors.objects.filter(
        ClimatiqActivityId=activity_id,
        CountryCode=region or None,
        ApplicableYear=year,
    ).first()
    if cached and cached.ExternalSyncedAt and cached.ExternalSyncedAt >= now() - STALE_AFTER:
        return cached

    result = fetch_climatiq_factor(activity_id=activity_id, region=region, year=year)
    if not result:
        return cached  # fall back to a stale cached row if the API is unavailable

    co2e = result.get("factor", {}).get("co2e")
    if co2e is None:
        return cached

    obj, _ = EmissionFactors.objects.update_or_create(
        ClimatiqActivityId=activity_id,
        CountryCode=region or None,
        ApplicableYear=year,
        defaults={
            "SetId": _get_climatiq_set(),
            "ActivityName": result.get("name", activity_id),
            "ActivityCategory": result.get("category"),
            "Scope": scope,
            "Gas": gas,
            "FactorValue": Decimal(str(co2e)),
            "ExternalSyncedAt": now(),
        },
    )
    return obj


def _refresh_factor(factor) -> bool:
    """Refresh one EmissionFactors row from Climatiq. Returns True if updated."""
    result = fetch_climatiq_factor(
        activity_id=factor.ClimatiqActivityId,
        region=factor.CountryCode or "",
        year=factor.ApplicableYear,
    )
    if not result:
        return False

    co2e = result.get("factor", {}).get("co2e")
    if co2e is None:
        return False

    factor.FactorValue = Decimal(str(co2e))
    factor.ExternalSyncedAt = now()
    factor.save(update_fields=["FactorValue", "ExternalSyncedAt"])
    return True


@shared_task(
    name="tasks.integrations.sync_climatiq_emission_factors",
    bind=True,
    max_retries=3,
    default_retry_delay=600,
)
def sync_climatiq_emission_factors(self):
    """
    Refresh Climatiq-sourced EmissionFactors whose cache is older than 7 days.
    Records are keyed by ClimatiqActivityId; only those with a non-null activity
    id are eligible. Idempotent and safe to re-run.
    """
    from apps.emissions.models import EmissionFactors

    if not _api_key():
        logger.warning("sync_climatiq_emission_factors: CLIMATIQ_API_KEY not configured, skipping")
        return {"skipped": "CLIMATIQ_API_KEY not configured"}

    cutoff = now() - STALE_AFTER
    stale = EmissionFactors.objects.filter(
        ClimatiqActivityId__isnull=False,
    ).filter(
        models.Q(ExternalSyncedAt__isnull=True) | models.Q(ExternalSyncedAt__lt=cutoff)
    )

    refreshed = 0
    errors = 0
    for factor in stale.iterator():
        try:
            if _refresh_factor(factor):
                refreshed += 1
        except Exception as exc:  # network / parse / DB — keep going, surface count
            logger.error("Climatiq refresh failed for factor %s: %s", factor.FactorId, exc)
            errors += 1

    logger.info("sync_climatiq_emission_factors: %d refreshed, %d errors", refreshed, errors)
    return {"refreshed": refreshed, "errors": errors}
