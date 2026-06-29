"""
Entities service layer.

API key generation lives here because it mixes cryptographic operations with
two model writes — that's domain logic, not a view concern.
"""
import hashlib
import secrets
from decimal import Decimal


# ── Organisational consolidation (ghg_calculation_spec §9) ──────────────────────

def _entity_scope_totals(entity_id: int, reporting_year: int) -> dict:
    """Standalone Scope 1/2/3 totals (tCO2e) for one entity + year.

    Scope 2 uses the market-based figure as the primary method (consistent with
    the inventory net-emissions calculation).
    """
    from django.db.models import Sum
    from apps.emissions.models import EmissionsData

    qs = EmissionsData.objects.filter(
        EntityId_id=entity_id, ReportingYear=reporting_year, Status__lt=4,
    )

    def _sum(scope, field="EmissionsAmountTonnes", divisor=Decimal("1")):
        value = qs.filter(Scope=scope).aggregate(t=Sum(field))["t"]
        return (Decimal(str(value or 0)) / divisor)

    scope1 = _sum(1)
    scope2 = _sum(2, "EmissionsAmountMarketBased", Decimal("1000"))
    scope3 = _sum(3)
    return _round_scopes({"scope1": scope1, "scope2": scope2, "scope3": scope3})


def _round_scopes(scopes: dict) -> dict:
    out = {k: (v or Decimal("0")).quantize(Decimal("0.000001")) for k, v in scopes.items()}
    out["total"] = (out["scope1"] + out["scope2"] + out["scope3"]).quantize(Decimal("0.000001"))
    return out


def compute_consolidated_emissions(*, entity, reporting_year: int, approach: int = None) -> dict:
    """
    Roll an entity's own emissions up with its subsidiaries' per GHG Protocol
    organisational consolidation (ghg_calculation_spec §9.3).

    approach: 1 = Equity Share (subsidiaries attributed by OwnershipSharePercent),
              2 = Financial Control, 3 = Operational Control (both 100%).
    Defaults to the entity's ConsolidationApproach, else Operational Control.
    """
    from apps.entities.models import Entities

    approach = approach or entity.ConsolidationApproach or 3

    own = _entity_scope_totals(entity.EntityId, reporting_year)
    consolidated = {"scope1": own["scope1"], "scope2": own["scope2"], "scope3": own["scope3"]}

    subsidiaries = []
    for sub in Entities.objects.filter(ParentEntityId=entity, Status__lt=4):
        standalone = _entity_scope_totals(sub.EntityId, reporting_year)
        if approach == 1:  # equity share → proportional
            share = (sub.OwnershipSharePercent or Decimal("0")) / Decimal("100")
        else:              # financial / operational control → 100%
            share = Decimal("1")

        attributed = _round_scopes({
            k: standalone[k] * share for k in ("scope1", "scope2", "scope3")
        })
        for k in ("scope1", "scope2", "scope3"):
            consolidated[k] += attributed[k]

        subsidiaries.append({
            "entity_id": sub.EntityId,
            "entity_name": sub.EntityName,
            "ownership_share_percent": sub.OwnershipSharePercent,
            "share_applied": share,
            "standalone": standalone,
            "attributed": attributed,
        })

    return {
        "entity_id": entity.EntityId,
        "entity_name": entity.EntityName,
        "reporting_year": reporting_year,
        "consolidation_approach": approach,
        "own_emissions": own,
        "subsidiaries": subsidiaries,
        "consolidated_totals": _round_scopes(consolidated),
    }


def generate_api_key(*, entity, created_by_user_id: int, name: str = "", expiry_date=None) -> dict:
    """
    Generate a new API key for an entity.

    Returns a dict with the raw key (shown once to the user), the prefix
    (stored in plaintext for identification), and the created record ID.
    The raw key is never stored — only a SHA-256 hash is persisted.

    Caller is responsible for returning the raw_key to the client exactly once.
    """
    from apps.shared.models import EntityApiKeys
    from apps.entities.models import EntityApiKeysIntermediary

    raw_key = secrets.token_urlsafe(32)
    hashed  = hashlib.sha256(raw_key.encode()).hexdigest()
    prefix  = raw_key[:8]

    key = EntityApiKeys.objects.create(
        EntityId          = entity.EntityId,
        HashedApiKey      = hashed,
        KeyPrefix         = prefix,
        ExpiryDate        = expiry_date,
        AuthorizedByFor   = name,
        CreatedBy         = created_by_user_id,
    )
    EntityApiKeysIntermediary.objects.create(EntityId=entity, ApiKeyId=key)

    return {
        "ApiKeyId":  key.ApiKeyId,
        "KeyPrefix": prefix,
        "RawKey":    raw_key,
        "ExpiryDate": key.ExpiryDate,
    }


def revoke_api_key(*, key) -> None:
    """Soft-delete an API key by setting Status = 4."""
    key.Status = 4
    key.save()


# ── Multi-entity access (G21) ───────────────────────────────────────────────────

def user_can_access_entity(user, entity_id) -> bool:
    """True if the user may operate in entity_id: SuperAdmin, their primary
    entity, or an EntityMembers grant."""
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "IsSuperAdmin", False):
        return True
    if getattr(user, "EntityId_id", None) == entity_id:
        return True
    from apps.entities.models import EntityMembers
    return EntityMembers.objects.filter(UserId=user, EntityId_id=entity_id).exists()


def accessible_entity_ids(user) -> set:
    """All entity ids the user can access (primary + memberships). Empty for SA
    (SuperAdmin is unrestricted and handled separately by callers)."""
    ids = set()
    primary = getattr(user, "EntityId_id", None)
    if primary:
        ids.add(primary)
    from apps.entities.models import EntityMembers
    ids.update(
        EntityMembers.objects.filter(UserId=user).values_list("EntityId_id", flat=True)
    )
    return ids
