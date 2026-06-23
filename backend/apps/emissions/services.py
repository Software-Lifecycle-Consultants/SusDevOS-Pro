"""
Emissions service layer.

All GHG calculation logic, verification state transitions, and audit writing
live here. Models and views delegate to these functions — they contain no
domain logic themselves.
"""
from decimal import Decimal

from django.utils import timezone


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
    qty = instance.QuantityCanonical or instance.QuantityOrCost
    ef  = instance.EmissionFactor
    gwp = _get_gwp_factor(instance)

    kg = qty * ef * gwp
    instance.EmissionsAmount       = kg.quantize(Decimal("0.0001"))
    instance.EmissionsAmountTonnes = (kg / Decimal("1000")).quantize(Decimal("0.000001"))

    if instance.Scope == 2:
        instance.EmissionsAmountLocationBased = instance.EmissionsAmount
        # Market-based: preserve any existing value (supplier EAC EF may differ);
        # only default to location-based if not yet set.
        if instance.EmissionsAmountMarketBased is None:
            instance.EmissionsAmountMarketBased = instance.EmissionsAmount


def _get_gwp_factor(instance) -> Decimal:
    """Look up GWP₁₀₀ for the gas/subtype combination. Defaults to 1 (CO₂-equivalent passthrough)."""
    try:
        return instance.GwpDatasetId.gwp_values.get(
            Gas=instance.Gas,
            GasSubtype=instance.GasSubtype or None,
        ).GwpFactor
    except Exception:
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
