"""
GHG inventory maintenance tasks.

Nightly tasks that keep GHGInventory totals current and link milestone actuals.
These run after business hours (01:00–01:30 UTC) to avoid contention.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

from django.db import models
from django.utils.timezone import now

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="tasks.emissions.recompute_stale_inventory_totals")
def recompute_stale_inventory_totals():
    """
    Find GHGInventories whose scope totals haven't been recomputed in 24h
    and refresh them. Catches any records that missed an inline invalidation.
    """
    from apps.emissions.models import GHGInventories

    stale_cutoff = now() - timedelta(hours=24)
    # Spec (celery_tasks.md): recompute inventories never computed OR last computed >24h ago.
    stale = GHGInventories.objects.filter(
        models.Q(TotalsLastComputedAt__isnull=True)
        | models.Q(TotalsLastComputedAt__lt=stale_cutoff),
        DeletedAt__isnull=True,
        VerificationStatus__lt=3,  # don't touch verified inventories
    )

    updated = 0
    errors = 0
    for inventory in stale:
        try:
            _compute_inventory_totals(inventory)
            updated += 1
        except Exception as exc:
            logger.error("Failed to recompute inventory %s: %s", inventory.InventoryId, exc)
            errors += 1

    logger.info(
        "recompute_stale_inventory_totals: %d updated, %d errors",
        updated,
        errors,
    )
    return {"updated": updated, "errors": errors}


def _compute_inventory_totals(inventory):
    """Aggregate records explicitly assigned to this inventory.

    Reporting year is descriptive metadata, not membership.  An entity may
    legitimately hold more than one inventory for the same year (for example a
    corrected version or a different boundary), so entity+year aggregation can
    contaminate both inventories and include unassigned working records.
    """
    from apps.emissions.models import EmissionsData, EmissionsOffsets

    base_qs = EmissionsData.objects.filter(
        EntityId=inventory.EntityId,
        InventoryId=inventory,
        Status__lt=4,
    )

    def _sum(scope, field="EmissionsAmountTonnes"):
        result = base_qs.filter(Scope=scope).aggregate(t=models.Sum(field))["t"]
        return Decimal(str(result or 0))

    scope1 = _sum(1)
    scope2l = _sum(2, "EmissionsAmountLocationBased") / Decimal("1000")
    scope2m = _sum(2, "EmissionsAmountMarketBased") / Decimal("1000")
    scope3 = _sum(3)

    # Only 'valid' credits reduce the net total — CLAUDE.md critical rule.
    # 'unverified', 'pending', and 'invalid' offsets must never be deducted.
    # Offsets inherit inventory membership from their linked emissions record.
    offsets = EmissionsOffsets.objects.filter(
        EntityId=inventory.EntityId,
        EmissionsId__InventoryId=inventory,
        Status__lt=4,
        RegistryValidationStatus="valid",
    ).aggregate(t=models.Sum("OffsetAmountTonnes"))["t"]

    total_offsets = Decimal(str(offsets or 0))

    # Net uses market-based Scope 2 as the primary method (GHG Protocol Scope 2
    # Guidance). Location-based remains stored for dual reporting.
    net = scope1 + scope2m + scope3 - total_offsets

    inventory.TotalScope1Tonnes = scope1
    inventory.TotalScope2LocationTonnes = scope2l
    inventory.TotalScope2MarketTonnes = scope2m
    inventory.TotalScope3Tonnes = scope3
    inventory.TotalOffsetsTonnes = total_offsets
    inventory.NetEmissionsTonnes = net
    inventory.TotalsLastComputedAt = now()
    inventory.save(
        update_fields=[
            "TotalScope1Tonnes",
            "TotalScope2LocationTonnes",
            "TotalScope2MarketTonnes",
            "TotalScope3Tonnes",
            "TotalOffsetsTonnes",
            "NetEmissionsTonnes",
            "TotalsLastComputedAt",
        ]
    )


@shared_task(name="tasks.emissions.link_milestone_actuals")
def link_milestone_actuals():
    """
    For each TargetMilestone where MilestoneYear has passed and actuals not yet linked,
    find the matching GHGInventory and populate ActualEmissionsTonnes + IsAchieved.
    """
    from apps.emissions.models import GHGInventories, TargetMilestones

    current_year = date.today().year

    milestones = TargetMilestones.objects.filter(
        MilestoneYear__lt=current_year,
        ActualEmissionsTonnes__isnull=True,
        Status__lt=4,
    ).select_related("TargetId__EntityId")

    linked = 0
    for milestone in milestones:
        entity = milestone.TargetId.EntityId

        inventory = GHGInventories.objects.filter(
            EntityId=entity,
            ReportingYear=milestone.MilestoneYear,
            NetEmissionsTonnes__isnull=False,
        ).first()

        if not inventory:
            continue

        actual = inventory.NetEmissionsTonnes or Decimal("0")
        target = milestone.TargetEmissionsTonnes

        milestone.ActualEmissionsTonnes = actual
        # `target is not None` (not truthiness): a net-zero milestone has
        # TargetEmissionsTonnes == 0, which is falsy — `target and ...` would
        # short-circuit and mark it never-achieved even when actual <= 0.
        milestone.IsAchieved = bool(target is not None and actual <= target)
        milestone.save(update_fields=["ActualEmissionsTonnes", "IsAchieved"])
        linked += 1

    logger.info("link_milestone_actuals: %d milestones linked", linked)
    return {"linked": linked}
