"""
Emissions service layer.

All GHG calculation logic, verification state transitions, and audit writing
live here. Models and views delegate to these functions — they contain no
domain logic themselves.
"""
import logging
from decimal import Decimal

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.utils import timezone

logger = logging.getLogger(__name__)

# ── GHG Calculation ───────────────────────────────────────────────────────────

def compute_emissions(instance) -> None:
    """
    Apply unit conversion then calculate EmissionsAmount fields.
    Mutates instance in place; the caller is responsible for saving.
    Called from EmissionsData.save() and directly for bulk recalculation.
    """
    if instance.QuantityOrCost is None or instance.EmissionFactor is None:
        return
    _apply_unit_conversion(instance)
    _compute_amounts(instance)


def _apply_unit_conversion(instance) -> None:
    """Populate QuantityCanonical using the input unit's ConversionFactor."""
    if instance.InputUnitId_id and instance.InputUnitId and instance.InputUnitId.ConversionFactor:
        instance.QuantityCanonical = instance.QuantityOrCost * instance.InputUnitId.ConversionFactor
    else:
        instance.QuantityCanonical = instance.QuantityOrCost


def _compute_amounts(instance) -> None:
    """
    Core formula: kg CO₂e = quantity × emission_factor × GWP₁₀₀
    Scope 2 always gets both location-based and market-based fields populated.
    Biogenic CO₂ is NOT included in EmissionsAmount (GHG Protocol §6.3).
    """
    # Use the unit-converted canonical quantity. `is None` (not truthiness): a
    # legitimately zero canonical value must not silently revert to the raw,
    # un-normalized QuantityOrCost.
    qty = instance.QuantityCanonical if instance.QuantityCanonical is not None else instance.QuantityOrCost
    ef  = instance.EmissionFactor
    gwp = _get_gwp_factor(instance)

    kg = qty * ef * gwp
    instance.EmissionsAmount       = kg.quantize(Decimal("0.0001"))
    instance.EmissionsAmountTonnes = (kg / Decimal("1000")).quantize(Decimal("0.000001"))

    # Biogenic CO2 (combustion of biomass/biofuels) — computed separately and
    # EXCLUDED from EmissionsAmount/GWP total (GHG Protocol §9, critical rule #4).
    if instance.BiogenicCO2FactorKg is not None:
        bio_kg = qty * instance.BiogenicCO2FactorKg
        instance.BiogenicCO2AmountTonnes = (bio_kg / Decimal("1000")).quantize(Decimal("0.000001"))
    else:
        # Factor cleared on a re-save must clear the derived figure too, otherwise
        # a stale biogenic amount is reported after the record stops being biogenic.
        instance.BiogenicCO2AmountTonnes = None

    if instance.Scope == 2:
        _compute_scope2(instance, qty)


def _compute_scope2(instance, qty) -> None:
    """
    Dual-method Scope 2 (GHG Protocol Scope 2 Guidance, critical rule #5).
    Uses separate EFLocationBased / EFMarketBased inputs when provided; falls back
    to the generic EmissionFactor result so legacy records still populate both.
    The primary EmissionsAmount uses market-based when available (GHG Protocol Scope 2 Guidance).
    """
    fallback = instance.EmissionsAmount  # qty × EmissionFactor × gwp, already computed

    # Location/Market amounts are server-computed (CALCULATED_FIELDS) and must be
    # recomputed on every save. Using `else` (not `elif ... is None`) keeps them
    # idempotent: on a re-save of a fallback record they refresh from the freshly
    # computed fallback instead of retaining a stale value from the prior save.
    if instance.EFLocationBased is not None:
        lb_kg = qty * instance.EFLocationBased
        instance.EmissionsAmountLocationBased = lb_kg.quantize(Decimal("0.0001"))
    else:
        instance.EmissionsAmountLocationBased = fallback

    if instance.EFMarketBased is not None:
        mb_kg = qty * instance.EFMarketBased
        instance.EmissionsAmountMarketBased = mb_kg.quantize(Decimal("0.0001"))
    else:
        instance.EmissionsAmountMarketBased = instance.EmissionsAmountLocationBased

    # Primary figure: market-based when available, else location-based.
    primary = instance.EmissionsAmountMarketBased
    if primary is None:
        primary = instance.EmissionsAmountLocationBased
    if primary is not None:
        instance.EmissionsAmount       = primary
        instance.EmissionsAmountTonnes = (primary / Decimal("1000")).quantize(Decimal("0.000001"))


def _get_gwp_factor(instance) -> Decimal:
    """
    Look up GWP₁₀₀ for the gas/subtype combination.

    A missing dataset yields the CO₂-equivalent passthrough (1). A *missing row*
    for a gas that does have GWP data is a data problem, not a passthrough: for
    non-CO₂ gases (CH₄ ≈ 30×, N₂O ≈ 273×) silently returning 1 would undercount
    the record by that factor, so we log it loudly instead of swallowing it. When
    a subtype was supplied but did not match (e.g. an errant subtype on a gas that
    is stored subtype-agnostically), we retry once without the subtype before
    falling back, rather than treating the miss as CO₂.
    """
    dataset = instance.GwpDatasetId
    if dataset is None:
        return Decimal("1")

    subtype = instance.GasSubtype or None
    try:
        return dataset.gwp_values.get(Gas=instance.Gas, GasSubtype=subtype).GwpFactor
    except ObjectDoesNotExist:
        if subtype is not None:
            # Retry subtype-agnostically — recovers a canonical (Gas, None) row.
            try:
                return dataset.gwp_values.get(Gas=instance.Gas, GasSubtype=None).GwpFactor
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                pass
        logger.warning(
            "GWP factor not found for gas=%r subtype=%r in dataset %s; "
            "falling back to 1 (record may be undercounted)",
            instance.Gas, subtype, getattr(dataset, "pk", dataset),
        )
        return Decimal("1")
    except MultipleObjectsReturned:
        logger.warning(
            "Multiple GWP factors match gas=%r subtype=%r in dataset %s; "
            "falling back to 1", instance.Gas, subtype, getattr(dataset, "pk", dataset),
        )
        return Decimal("1")


# ── Verification state transitions ────────────────────────────────────────────

def verify_record(instance, verified_by, notes: str = "") -> None:
    """
    Advance VerificationStatus to VERIFIED (3).
    Records verifier identity and timestamp. Caller must check current status
    before calling — this function does not guard against double-verification.
    """
    instance.VerificationStatus = 3
    instance.VerifiedBy         = verified_by
    instance.VerifiedAt         = timezone.now()
    instance.VerificationNotes  = notes
    instance.save()

    from apps.notifications.services import notify
    notify(
        user_id=instance.CreatedBy,
        entity_id=instance.EntityId_id,
        type="emissions_verified",
        title="Emissions record verified",
        body=f"'{instance.Title}' has been verified and is now locked.",
        related_module="emissions",
        related_record_id=instance.EmissionsId,
    )


def unlock_record(instance, reason: str, unlocked_by, entity_id: int) -> None:
    """
    Reset VerificationStatus to 1 (Submitted/Under review) after it reached
    VERIFIED. Writes a mandatory 7-year retention audit log entry.
    Only callable by SuperAdmin — the view enforces that guard.
    """
    from apps.shared.models import AuditLog

    instance.VerificationStatus = 1
    instance.save()

    AuditLog.objects.create(
        EntityId_id       = entity_id,
        ChangedBy         = unlocked_by,
        ChangedByUsername = unlocked_by.username,
        Action            = "Unlock_Verified",
        TableName         = "emissions_data",
        RecordId          = instance.EmissionsId,
        Description       = f"Unlocked verified record. Reason: {reason}",
        RetentionTier     = 3,  # 7-year regulatory retention (CLAUDE.md §compliance)
    )

    from apps.notifications.services import notify
    notify(
        user_id=instance.CreatedBy,
        entity_id=entity_id,
        type="emissions_unlocked",
        title="Verified record unlocked",
        body=f"'{instance.Title}' was unlocked for editing. Reason: {reason}",
        related_module="emissions",
        related_record_id=instance.EmissionsId,
    )
