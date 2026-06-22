# Pricing Model Specification — SusDevOS

---

## Model Summary

**Entity-based freemium** with module gating and a seat limit per tier. Billing is per entity subscription (one plan per entity). The ESG consultant use case is served by the Agency plan, which allows one account to manage many entities.

**Why entity-based, not seat-based:**
Sustainability managers are often solo or in a team of 2. Seat pricing undercharges large organisations (who have few sustainability staff) and overcharges consultants (who need many logins). Entity count scales with organisational complexity, which is a much better proxy for the value delivered.

---

## Tiers

### Free
**Price:** £0/month, forever. No credit card required.
**Intended user:** A small company or sole trader doing their first GHG inventory, or someone evaluating the tool before committing.
**Limits:** 1 entity, 1 reporting year (current year only), 1 user, Scope 1 + 2 only.

### Starter
**Price:** £49/month (£39/month billed annually — 20% saving)
**Intended user:** An SME with a single entity that needs a full annual GHG inventory including Scope 3.
**Limits:** 1 entity, 3 years of data, 5 users, all Scopes.

### Professional
**Price:** £199/month (£159/month billed annually)
**Intended user:** A mid-size company with subsidiaries, or an ESG manager who needs verification workflows and SBTi tracking.
**Limits:** 5 entities, unlimited years, 20 users, all modules.
**Entity add-on:** £25/month per additional entity beyond 5.

### Agency
**Price:** £499/month (£399/month billed annually)
**Intended user:** Sustainability consultancies managing multiple client inventories.
**Limits:** 25 entities, unlimited users, white-label reports, client portal.
**Entity add-on:** £15/month per additional entity beyond 25.

### Enterprise
**Price:** Custom (annual contract, minimum £24,000/year)
**Intended user:** Large corporates, government bodies, organizations needing data residency, SSO, or a dedicated instance.
**Limits:** Unlimited entities, unlimited users, all features, custom SLA.

---

## Feature Gate Matrix

`✓` = included, `—` = not available, `↑` = upgrade prompt shown

| Feature | Free | Starter | Professional | Agency | Enterprise |
|---------|------|---------|-------------|--------|------------|
| **Entities** | 1 | 1 | 5 | 25 | Unlimited |
| **Users per entity** | 1 | 5 | 20 | Unlimited | Unlimited |
| **Reporting years** | 1 (current) | 3 | Unlimited | Unlimited | Unlimited |
| **Scope 1** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Scope 2 (location-based)** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Scope 2 (market-based)** | — ↑ | ✓ | ✓ | ✓ | ✓ |
| **Scope 3 (all 15 categories)** | — ↑ | ✓ | ✓ | ✓ | ✓ |
| **Scope 3 relevance assessment** | — ↑ | ✓ | ✓ | ✓ | ✓ |
| **Emission factor library (DEFRA/EPA/Climatiq)** | ✓ (DEFRA only) | ✓ | ✓ | ✓ | ✓ |
| **GHG inventory (formal, versioned)** | — ↑ | ✓ | ✓ | ✓ | ✓ |
| **GWP dataset selection (AR4/AR5/AR6)** | — | ✓ | ✓ | ✓ | ✓ |
| **SBTi target setting** | — ↑ | ✓ | ✓ | ✓ | ✓ |
| **SBTi milestone tracking** | — | ✓ | ✓ | ✓ | ✓ |
| **SBTi registry sync** | — | — | ✓ | ✓ | ✓ |
| **Ecosystem tracking (basic)** | — ↑ | ✓ | ✓ | ✓ | ✓ |
| **IPCC biomass carbon (Tier 1)** | — | ✓ | ✓ | ✓ | ✓ |
| **IPCC biomass carbon (Tier 2/3)** | — | — ↑ | ✓ | ✓ | ✓ |
| **Restoration sequestration** | — | ✓ | ✓ | ✓ | ✓ |
| **Land parcel mapping (GIS)** | — | — ↑ | ✓ | ✓ | ✓ |
| **TNFD-aligned reporting** | — | — | ✓ | ✓ | ✓ |
| **Internal approval workflow** | — ↑ | — ↑ | ✓ | ✓ | ✓ |
| **Third-party verification support** | — | — | ✓ | ✓ | ✓ |
| **Carbon offset management** | — | ✓ | ✓ | ✓ | ✓ |
| **Offset registry validation (Verra/GS)** | — | — ↑ | ✓ | ✓ | ✓ |
| **Companies House auto-populate** | — | ✓ | ✓ | ✓ | ✓ |
| **FX conversion for spend-based EFs** | — | ✓ | ✓ | ✓ | ✓ |
| **PDF report (watermarked)** | ✓ | — | — | — | — |
| **PDF report (unbranded)** | — | ✓ | ✓ | — | — |
| **PDF report (white-label)** | — | — | — ↑ | ✓ | ✓ |
| **CSV / JSON export** | — | ✓ | ✓ | ✓ | ✓ |
| **CDP export format** | — | — ↑ | ✓ | ✓ | ✓ |
| **Audit log (30 days)** | ✓ | ✓ | — | — | — |
| **Audit log (1 year)** | — | — | ✓ | ✓ | — |
| **Audit log (7 years)** | — | — | — | — | ✓ |
| **Blog (public-facing)** | ✓ (1 author) | ✓ | ✓ | ✓ | ✓ |
| **Entity API keys** | — | — ↑ | ✓ | ✓ | ✓ |
| **API access (rate limited)** | — | — | 500/day | 2,000/day | Custom |
| **Client read-only portal** | — | — | — ↑ | ✓ | ✓ |
| **Multi-entity dashboard** | — | — | ✓ | ✓ | ✓ |
| **Bulk data import (CSV)** | — | — | ✓ | ✓ | ✓ |
| **User privilege overrides** | — | — | ✓ | ✓ | ✓ |
| **SSO / SAML** | — | — | — | — | ✓ |
| **Dedicated instance** | — | — | — | — | ✓ |
| **Custom data residency** | — | — | — | — | ✓ |
| **SLA** | — | — | — | 99.5% | 99.9% |
| **Support** | Docs only | Email (48h) | Email (24h) | Priority (8h) | Dedicated CSM |

---

## Upgrade Prompt Triggers

Upgrade prompts appear contextually — at the moment a user tries to use a gated feature. They are non-blocking (the user can dismiss and continue with available features). Each prompt explains the specific benefit they'd unlock.

### In-product upgrade moments

**Scope 2 market-based (Free → Starter)**
Trigger: User adds a Scope 2 emission record and selects "Market-based method".
Prompt: *"Market-based Scope 2 is required for SBTi target reporting. Available on Starter (£49/month)."*
CTA: `Upgrade to Starter` / `Learn why this matters`

**Scope 3 (Free → Starter)**
Trigger: User tries to add an emission record with Scope = 3.
Prompt: *"Scope 3 covers your supply chain and can account for over 70% of a company's total footprint. Unlock all 15 categories on Starter."*
CTA: `Upgrade to Starter`

**Formal GHG inventory (Free → Starter)**
Trigger: User tries to create a GHGInventory record (required for verification).
Prompt: *"A formal GHG inventory is required for CDP submission and third-party verification. Available on Starter."*

**Second reporting year (Free → Starter)**
Trigger: User tries to view or add data for a year other than the current year.
Prompt: *"Compare year-on-year progress by unlocking historical data. Available on Starter."*

**Verification workflow (Starter → Professional)**
Trigger: User tries to submit an inventory for review or set VerificationStatus.
Prompt: *"Internal approval workflows and third-party verification support require Professional. Your verifier can sign off directly in SusDevOS."*
CTA: `Upgrade to Professional`

**Land parcel mapping (Starter → Professional)**
Trigger: User tries to create a LandParcel record with polygon geometry.
Prompt: *"GIS land parcel mapping with PostGIS geometry is available on Professional. Map your project footprint precisely."*

**IPCC Tier 2/3 biomass (Starter → Professional)**
Trigger: User selects BiomassCalculationMethod = 2 or 3.
Prompt: *"Country-specific and allometric biomass calculations require Professional. Tier 1 (IPCC global defaults) is available on your current plan."*

**White-label reports (Professional → Agency)**
Trigger: User opens Report Settings and looks for logo/branding options.
Prompt: *"White-label PDF reports with your company or client branding are available on the Agency plan — designed for sustainability consultants."*

**6th entity (Professional limit reached)**
Trigger: User tries to create a 6th entity.
Prompt: *"You've reached your entity limit. Add more entities at £25/month each, or upgrade to Agency for up to 25 entities at £499/month."*
Two CTAs: `Add entity (£25/month)` / `Upgrade to Agency`

**Client portal (Professional → Agency)**
Trigger: User tries to invite someone with a "Client (read-only)" role.
Prompt: *"A client-facing read-only portal, where clients can view their own entity's data without accessing yours, is available on Agency."*

### Email-triggered upgrade prompts (Celery tasks)

These are sent by `tasks.billing.send_upgrade_nudge` — triggered by usage patterns, not just hard limits.

**"You've been on Free for 30 days"** — sent 30 days after registration if still on Free.
Subject: `Your Scope 1 & 2 data is in — here's what you're missing`
Body: Summary of their current data + specific Scope 3 categories relevant to their industry (from SIC codes) that they haven't captured.

**"Your inventory is 80% complete"** — sent when all Scope 1+2 categories have data but Scope 3 doesn't (Free plan).
Subject: `You're nearly there — your Scope 3 is missing`

**"Year-end approaching"** — sent 1 November each year to Free users.
Subject: `Your [year] GHG inventory closes in 60 days`
Body: Prompt to upgrade before year-end data entry crunch.

**"New DEFRA factors available"** — sent March/April when DEFRA EFs update.
Subject: `DEFRA [year] emission factors are now available`
Body: Summary of what changed + note that Starter+ plans get auto-updated EFs.

---

## Billing Logic

### Stripe integration

All billing via Stripe. Key objects:
- `stripe.Customer` — created at entity registration, `StripeCustomerId` stored on `EntitySubscriptions`
- `stripe.Subscription` — one per entity per billing period
- `stripe.Price` — one price object per tier per billing interval (monthly/annual)
- `stripe.Invoice` — generated monthly or annually by Stripe

### Trial

14-day free trial on Starter and Professional, no credit card required. Trial starts at upgrade click. If card not added before trial ends, entity reverts to Free (data retained).

`EntitySubscriptions.TrialEndsAt` — set to 14 days from upgrade date. Celery task `tasks.billing.check_trial_expiry` runs daily and handles reversion.

### Annual billing discount

Annual prices at 20% discount. Stripe handles this via separate `Price` objects with `interval=year`. Switching from monthly to annual: Stripe prorates the remaining monthly period as a credit.

### Entity add-ons

Additional entities beyond tier limit billed as Stripe `SubscriptionItem` add-ons on the primary subscription. Quantity = number of extra entities. Price: £25/entity/month (Professional), £15/entity/month (Agency).

When an entity is deleted or archived, remove the corresponding `SubscriptionItem`. Stripe prorates the credit automatically.

### Dunning (failed payment handling)

Stripe Smart Retries handles initial retries (days 1, 3, 5, 7). After all retries exhausted:
1. Day 8: `EntitySubscriptions.Status` → `past_due`. User shown a payment banner on every page. No features removed yet.
2. Day 15: Plan reverted to Free. Data retained but export blocked until payment resolved (to avoid data dumping before cancellation).
3. Day 90 post-cancellation: Hard delete of entity data (preceded by 30-day email warning).

---

## Plan Enforcement — Application Layer

Feature gate checks are done in a reusable Django mixin. Never rely on client-side checks alone.

```python
# apps/billing/mixins.py

from apps.billing.models import EntitySubscriptions, PlanFeatures

class FeatureGateMixin:
    """
    Add to any APIView or ViewSet to enforce plan-based feature gates.

    Usage:
        class EmissionsDataViewSet(FeatureGateMixin, viewsets.ModelViewSet):
            required_feature = "scope_3"
    """
    required_feature: str = None

    def get_entity_plan(self):
        entity_id = self.request.entity_id   # set by TenantQueryMiddleware
        sub = EntitySubscriptions.objects.filter(
            EntityId=entity_id,
            Status__in=["active", "trialing"],
        ).select_related("PlanId").first()
        return sub.PlanId if sub else None

    def check_feature_gate(self, feature_key: str) -> bool:
        plan = self.get_entity_plan()
        if not plan:
            return False   # no active subscription = Free plan
        gate = PlanFeatures.objects.filter(
            PlanId=plan,
            FeatureKey=feature_key,
            IsEnabled=True,
        ).exists()
        return gate

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if self.required_feature and not self.check_feature_gate(self.required_feature):
            plan = self.get_entity_plan()
            raise PermissionDenied({
                "code": "feature_gated",
                "feature": self.required_feature,
                "current_plan": plan.PlanName if plan else "free",
                "upgrade_url": "/pricing",
                "message": PlanFeatures.objects.filter(
                    FeatureKey=self.required_feature
                ).values_list("UpgradeMessage", flat=True).first()
            })
```

The frontend reads the `"code": "feature_gated"` response and renders the contextual upgrade modal rather than a generic error.

---

## Non-Profit and Academic Discount

Apply via `/contact` with subject "Discount request". Manual approval by admin. Once approved:
1. Create a Stripe coupon: `50_percent_off_forever`
2. Apply to customer's subscription: `stripe.Subscription.modify(sub_id, coupon=coupon_id)`
3. Set `EntitySubscriptions.DiscountCode = "nonprofit_50"` for internal tracking

Eligible: registered charities, NGOs, academic institutions. Government entities are not eligible (use Enterprise pricing).

---

## Revenue Model Projections (Reference)

Not prescriptive — illustrative assumptions for planning purposes.

| Scenario | Entities (paid) | Mix | MRR |
|----------|----------------|-----|-----|
| Early (Year 1) | 50 | 30 Starter, 15 Pro, 5 Agency | £13,420 |
| Growth (Year 2) | 250 | 120 Starter, 100 Pro, 25 Agency, 5 Enterprise | £89,500 |
| Scale (Year 3) | 1,000 | 400 Starter, 450 Pro, 120 Agency, 30 Enterprise | £395,000 |

Enterprise ACV assumed at £30,000 average.

Key metric to track: **conversion from Free → Starter**. Target: 8–12% of active Free entities within 90 days of signup. Main driver is completing the guided onboarding and hitting a feature gate in context.

---

## Seeded Plan Data

The `0028_plans_subscriptions.py` migration seeds all five plans and their feature gates. Plan prices are stored in the DB but billing is authoritative in Stripe — the DB price is for display only. `StripePriceIdMonthly` and `StripePriceIdAnnual` FKs hold the Stripe Price IDs configured during deployment.
