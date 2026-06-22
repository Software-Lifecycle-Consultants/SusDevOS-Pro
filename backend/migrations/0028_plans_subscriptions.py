"""
Migration: Plans, PlanFeatures, EntitySubscriptions, UsageTracking
App: apps.billing (new app)
Depends on: entities.0001_entities, users.0001_users_roles

Implements the entity-based freemium pricing model defined in spec/pricing.md.

Tables:
  Plans              — plan definitions (Free, Starter, Professional, Agency, Enterprise)
  PlanFeatures       — feature gate config per plan (what each plan can access)
  EntitySubscriptions — which plan each entity is currently on + Stripe references
  UsageTracking      — current-period usage counters (entities, users, API calls, years)

Enforcement:
  Feature gate checks are done in apps/billing/mixins.py (FeatureGateMixin).
  Hard limits (entity count, user count) are enforced on object creation via signals
  and serializer validation — never trust the frontend.

Seeded plans and feature gates are inserted in the post-migration data operation
at the bottom of this file. Stripe Price IDs are NOT seeded here — they are set
via admin after Stripe products are created in the Stripe Dashboard.
"""

from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


# ── Plan seed data ─────────────────────────────────────────────────────────────

PLANS = [
    {
        "PlanKey":          "free",
        "PlanName":         "Free",
        "PriceMonthlyGBP":  0,
        "PriceAnnualGBP":   0,
        "MaxEntities":      1,
        "MaxUsersPerEntity":1,
        "MaxReportingYears":1,
        "MaxApiCallsPerDay":0,
        "SupportTier":      "docs",
        "IsPublic":         True,
        "SortOrder":        1,
    },
    {
        "PlanKey":          "starter",
        "PlanName":         "Starter",
        "PriceMonthlyGBP":  49,
        "PriceAnnualGBP":   470,   # £39/month × 12
        "MaxEntities":      1,
        "MaxUsersPerEntity":5,
        "MaxReportingYears":3,
        "MaxApiCallsPerDay":0,
        "SupportTier":      "email_48h",
        "IsPublic":         True,
        "SortOrder":        2,
    },
    {
        "PlanKey":          "professional",
        "PlanName":         "Professional",
        "PriceMonthlyGBP":  199,
        "PriceAnnualGBP":   1908,  # £159/month × 12
        "MaxEntities":      5,
        "MaxUsersPerEntity":20,
        "MaxReportingYears":0,     # 0 = unlimited
        "MaxApiCallsPerDay":500,
        "SupportTier":      "email_24h",
        "IsPublic":         True,
        "SortOrder":        3,
    },
    {
        "PlanKey":          "agency",
        "PlanName":         "Agency",
        "PriceMonthlyGBP":  499,
        "PriceAnnualGBP":   4788,  # £399/month × 12
        "MaxEntities":      25,
        "MaxUsersPerEntity":0,     # 0 = unlimited
        "MaxReportingYears":0,
        "MaxApiCallsPerDay":2000,
        "SupportTier":      "priority_8h",
        "IsPublic":         True,
        "SortOrder":        4,
    },
    {
        "PlanKey":          "enterprise",
        "PlanName":         "Enterprise",
        "PriceMonthlyGBP":  0,     # custom — set per contract
        "PriceAnnualGBP":   0,
        "MaxEntities":      0,     # unlimited
        "MaxUsersPerEntity":0,
        "MaxReportingYears":0,
        "MaxApiCallsPerDay":0,
        "SupportTier":      "dedicated_csm",
        "IsPublic":         False,  # not shown on pricing page; sales-led
        "SortOrder":        5,
    },
]


# Feature keys and which plans include them.
# Format: (feature_key, upgrade_message, plans_with_access, limit_value_per_plan)
# limit_value=None means boolean gate (on/off).
# limit_value=N means a numeric limit (e.g. MaxEntities is handled in Plans,
# but some features have their own numeric limit).

FEATURE_GATES = [
    # ── Scopes ────────────────────────────────────────────────────────────────
    ("scope_1",
     "Scope 1 direct emissions are available on all plans.",
     ["free", "starter", "professional", "agency", "enterprise"],
     None),

    ("scope_2_location_based",
     "Location-based Scope 2 is available on all plans.",
     ["free", "starter", "professional", "agency", "enterprise"],
     None),

    ("scope_2_market_based",
     "Market-based Scope 2 is required for SBTi reporting. Upgrade to Starter.",
     ["starter", "professional", "agency", "enterprise"],
     None),

    ("scope_3",
     "Scope 3 covers your supply chain emissions across all 15 GHG Protocol categories. Upgrade to Starter.",
     ["starter", "professional", "agency", "enterprise"],
     None),

    ("scope_3_relevance_assessment",
     "Scope 3 relevance assessments are required for a GHG Protocol-conformant inventory. Upgrade to Starter.",
     ["starter", "professional", "agency", "enterprise"],
     None),

    # ── Emission factors ───────────────────────────────────────────────────────
    ("ef_library_defra",
     "DEFRA emission factors are available on all plans.",
     ["free", "starter", "professional", "agency", "enterprise"],
     None),

    ("ef_library_full",
     "The full emission factor library (DEFRA, EPA, Climatiq, IPCC) is available on Starter.",
     ["starter", "professional", "agency", "enterprise"],
     None),

    ("ef_auto_update",
     "Automatic annual emission factor updates are available on Starter.",
     ["starter", "professional", "agency", "enterprise"],
     None),

    # ── GHG inventory ─────────────────────────────────────────────────────────
    ("ghg_inventory_formal",
     "Formal versioned GHG inventories (required for CDP and verification) are available on Starter.",
     ["starter", "professional", "agency", "enterprise"],
     None),

    ("gwp_dataset_selection",
     "GWP dataset selection (AR4/AR5/AR6) is available on Starter.",
     ["starter", "professional", "agency", "enterprise"],
     None),

    ("multiple_reporting_years",
     "Access historical reporting years and year-on-year comparisons on Starter.",
     ["starter", "professional", "agency", "enterprise"],
     None),

    # ── Targets ───────────────────────────────────────────────────────────────
    ("sbti_targets",
     "SBTi target setting and milestone tracking are available on Starter.",
     ["starter", "professional", "agency", "enterprise"],
     None),

    ("sbti_registry_sync",
     "Automatic SBTi registry validation sync is available on Professional.",
     ["professional", "agency", "enterprise"],
     None),

    # ── Ecosystem & nature ────────────────────────────────────────────────────
    ("ecosystem_basic",
     "Ecosystem tracking (species, tree removals, restorations) is available on Starter.",
     ["starter", "professional", "agency", "enterprise"],
     None),

    ("ipcc_biomass_tier1",
     "IPCC Tier 1 biomass carbon calculations are available on Starter.",
     ["starter", "professional", "agency", "enterprise"],
     None),

    ("ipcc_biomass_tier2_tier3",
     "IPCC Tier 2 and Tier 3 biomass calculations require Professional.",
     ["professional", "agency", "enterprise"],
     None),

    ("land_parcel_gis",
     "GIS land parcel mapping with PostGIS geometry requires Professional.",
     ["professional", "agency", "enterprise"],
     None),

    ("tnfd_reporting",
     "TNFD-aligned biodiversity reporting requires Professional.",
     ["professional", "agency", "enterprise"],
     None),

    # ── Verification & workflow ───────────────────────────────────────────────
    ("internal_approval_workflow",
     "Internal approval workflows (Draft → Submitted → Reviewed → Approved) require Professional.",
     ["professional", "agency", "enterprise"],
     None),

    ("third_party_verification",
     "Third-party verification support (ISO 14064-3, ISAE 3410) requires Professional.",
     ["professional", "agency", "enterprise"],
     None),

    # ── Offsets ───────────────────────────────────────────────────────────────
    ("carbon_offsets",
     "Carbon offset management is available on Starter.",
     ["starter", "professional", "agency", "enterprise"],
     None),

    ("offset_registry_validation",
     "Automatic Verra and Gold Standard registry validation requires Professional.",
     ["professional", "agency", "enterprise"],
     None),

    # ── Integrations ──────────────────────────────────────────────────────────
    ("companies_house_lookup",
     "Companies House auto-population is available on Starter.",
     ["starter", "professional", "agency", "enterprise"],
     None),

    ("fx_conversion",
     "FX conversion for spend-based Scope 3 is available on Starter.",
     ["starter", "professional", "agency", "enterprise"],
     None),

    # ── Reports ───────────────────────────────────────────────────────────────
    ("report_pdf_watermarked",
     "Watermarked PDF reports are available on the Free plan.",
     ["free"],
     None),

    ("report_pdf_unbranded",
     "Unbranded PDF reports are available on Starter.",
     ["starter", "professional"],
     None),

    ("report_pdf_white_label",
     "White-label PDF reports with your branding are available on Agency.",
     ["agency", "enterprise"],
     None),

    ("report_csv_json_export",
     "CSV and JSON data export is available on Starter.",
     ["starter", "professional", "agency", "enterprise"],
     None),

    ("report_cdp_export",
     "CDP-formatted export requires Professional.",
     ["professional", "agency", "enterprise"],
     None),

    # ── Audit log retention ───────────────────────────────────────────────────
    ("audit_log_30d",
     "30-day audit log is available on all plans.",
     ["free", "starter"],
     None),

    ("audit_log_1yr",
     "1-year audit log retention is available on Professional.",
     ["professional", "agency"],
     None),

    ("audit_log_7yr",
     "7-year audit log retention is available on Enterprise.",
     ["enterprise"],
     None),

    # ── API ───────────────────────────────────────────────────────────────────
    ("api_access",
     "API access (entity-scoped keys) requires Professional.",
     ["professional", "agency", "enterprise"],
     None),

    # ── Agency / multi-tenant ────────────────────────────────────────────────
    ("client_portal",
     "A client read-only portal requires Agency.",
     ["agency", "enterprise"],
     None),

    ("white_label_branding",
     "White-label branding (logo, colours) requires Agency.",
     ["agency", "enterprise"],
     None),

    ("bulk_data_import",
     "Bulk CSV import requires Professional.",
     ["professional", "agency", "enterprise"],
     None),

    ("multi_entity_dashboard",
     "A unified multi-entity dashboard requires Professional.",
     ["professional", "agency", "enterprise"],
     None),

    ("user_privilege_overrides",
     "Per-user privilege overrides require Professional.",
     ["professional", "agency", "enterprise"],
     None),

    # ── Enterprise ────────────────────────────────────────────────────────────
    ("sso_saml",
     "SSO/SAML authentication requires Enterprise.",
     ["enterprise"],
     None),

    ("dedicated_instance",
     "A dedicated instance with custom data residency requires Enterprise.",
     ["enterprise"],
     None),
]


def seed_plans_and_features(apps, schema_editor):
    Plans = apps.get_model("billing", "Plans")
    PlanFeatures = apps.get_model("billing", "PlanFeatures")

    plan_objects = {}
    for plan_data in PLANS:
        p = Plans.objects.create(**plan_data)
        plan_objects[p.PlanKey] = p

    for feature_key, upgrade_message, plan_keys, limit_value in FEATURE_GATES:
        for plan_key in plan_keys:
            PlanFeatures.objects.create(
                PlanId=plan_objects[plan_key],
                FeatureKey=feature_key,
                IsEnabled=True,
                LimitValue=limit_value,
                UpgradeMessage=upgrade_message,
            )


def seed_free_subscriptions(apps, schema_editor):
    """
    Ensure every existing entity has at least a Free plan subscription.
    New entities get a Free subscription created automatically via a post_save signal.
    """
    Entities = apps.get_model("entities", "Entities")
    Plans = apps.get_model("billing", "Plans")
    EntitySubscriptions = apps.get_model("billing", "EntitySubscriptions")

    free_plan = Plans.objects.filter(PlanKey="free").first()
    if not free_plan:
        return

    for entity in Entities.objects.filter(DeletedAt__isnull=True):
        EntitySubscriptions.objects.get_or_create(
            EntityId=entity,
            defaults={
                "PlanId": free_plan,
                "Status": "active",
                "BillingInterval": "monthly",
                "CurrentPeriodStart": timezone.now(),
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ("entities", "0001_entities"),
        ("users", "0001_users_roles"),
    ]

    operations = [

        # ── Plans ─────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name="Plans",
            fields=[
                ("PlanId", models.AutoField(primary_key=True)),
                ("PlanKey", models.CharField(
                    max_length=50, unique=True,
                    help_text="Stable identifier used in code (free, starter, professional, agency, enterprise)"
                )),
                ("PlanName", models.CharField(max_length=100)),
                ("PriceMonthlyGBP", models.PositiveIntegerField(
                    help_text="Monthly price in GBP pence × 100 (e.g. 4900 = £49.00). 0 = free or custom."
                )),
                ("PriceAnnualGBP", models.PositiveIntegerField(
                    help_text="Annual price in GBP pence × 100. Represents total year cost."
                )),
                ("MaxEntities", models.PositiveSmallIntegerField(
                    help_text="Maximum entities on this plan. 0 = unlimited."
                )),
                ("MaxUsersPerEntity", models.PositiveSmallIntegerField(
                    help_text="Maximum users per entity. 0 = unlimited."
                )),
                ("MaxReportingYears", models.PositiveSmallIntegerField(
                    help_text="Maximum historical reporting years. 0 = unlimited. 1 = current year only."
                )),
                ("MaxApiCallsPerDay", models.PositiveIntegerField(
                    default=0,
                    help_text="Daily API call limit. 0 = no API access."
                )),
                ("AdditionalEntityPriceGBP", models.PositiveIntegerField(
                    default=0,
                    help_text=(
                        "Monthly price per entity beyond MaxEntities, in GBP pence × 100. "
                        "e.g. 2500 = £25.00. 0 = no add-ons available."
                    )
                )),
                ("SupportTier", models.CharField(
                    max_length=50,
                    help_text="docs | email_48h | email_24h | priority_8h | dedicated_csm"
                )),
                ("IsPublic", models.BooleanField(
                    default=True,
                    help_text="Show on /pricing page. False for Enterprise (sales-led)."
                )),
                ("SortOrder", models.PositiveSmallIntegerField(default=0)),
                ("StripePriceIdMonthly", models.CharField(
                    max_length=100, null=True, blank=True,
                    help_text="Stripe Price ID for monthly billing (price_xxx). Set after Stripe product creation."
                )),
                ("StripePriceIdAnnual", models.CharField(
                    max_length=100, null=True, blank=True,
                    help_text="Stripe Price ID for annual billing."
                )),
                ("CreatedAt", models.DateTimeField(auto_now_add=True)),
                ("UpdatedAt", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "plans"},
        ),

        # ── PlanFeatures ──────────────────────────────────────────────────────
        migrations.CreateModel(
            name="PlanFeatures",
            fields=[
                ("PlanFeatureId", models.AutoField(primary_key=True)),
                ("PlanId", models.ForeignKey(
                    "billing.Plans",
                    on_delete=models.CASCADE,
                    related_name="features",
                )),
                ("FeatureKey", models.CharField(
                    max_length=100,
                    help_text=(
                        "Stable feature identifier used in FeatureGateMixin.required_feature. "
                        "e.g. 'scope_3', 'land_parcel_gis', 'white_label_branding'"
                    )
                )),
                ("IsEnabled", models.BooleanField(default=True)),
                ("LimitValue", models.PositiveIntegerField(
                    null=True, blank=True,
                    help_text="Numeric limit for this feature on this plan. NULL = boolean gate (on/off)."
                )),
                ("UpgradeMessage", models.TextField(
                    help_text="Shown to users when they hit this feature gate. Explains what upgrading unlocks."
                )),
            ],
            options={"db_table": "plan_features"},
        ),
        migrations.AddConstraint(
            model_name="PlanFeatures",
            constraint=models.UniqueConstraint(
                fields=["PlanId", "FeatureKey"],
                name="unique_feature_per_plan"
            ),
        ),
        migrations.AddIndex(
            model_name="PlanFeatures",
            index=models.Index(
                fields=["PlanId", "FeatureKey"],
                name="idx_plan_feature_key"
            ),
        ),

        # ── EntitySubscriptions ───────────────────────────────────────────────
        migrations.CreateModel(
            name="EntitySubscriptions",
            fields=[
                ("SubscriptionId", models.AutoField(primary_key=True)),
                ("EntityId", models.OneToOneField(
                    "entities.Entities",
                    on_delete=models.PROTECT,
                    related_name="subscription",
                    help_text="One subscription per entity."
                )),
                ("PlanId", models.ForeignKey(
                    "billing.Plans",
                    on_delete=models.PROTECT,
                    related_name="subscriptions",
                )),
                ("Status", models.CharField(
                    max_length=20,
                    choices=[
                        ("active",     "Active"),
                        ("trialing",   "Trial"),
                        ("past_due",   "Past Due — payment failed, grace period"),
                        ("canceled",   "Canceled"),
                        ("incomplete", "Incomplete — awaiting initial payment"),
                    ],
                    default="active",
                )),
                ("BillingInterval", models.CharField(
                    max_length=10,
                    choices=[("monthly", "Monthly"), ("annual", "Annual")],
                    default="monthly",
                )),
                ("TrialEndsAt", models.DateTimeField(
                    null=True, blank=True,
                    help_text="Set to 14 days after upgrade for Starter/Professional trials."
                )),
                ("CurrentPeriodStart", models.DateTimeField(null=True, blank=True)),
                ("CurrentPeriodEnd", models.DateTimeField(null=True, blank=True)),
                ("CanceledAt", models.DateTimeField(null=True, blank=True)),
                ("CancelAtPeriodEnd", models.BooleanField(
                    default=False,
                    help_text="If True, subscription cancels at CurrentPeriodEnd (user requested downgrade)."
                )),
                # Stripe references
                ("StripeCustomerId", models.CharField(
                    max_length=100, null=True, blank=True,
                    help_text="Stripe Customer ID (cus_xxx)"
                )),
                ("StripeSubscriptionId", models.CharField(
                    max_length=100, null=True, blank=True,
                    help_text="Stripe Subscription ID (sub_xxx)"
                )),
                ("StripeLatestInvoiceId", models.CharField(
                    max_length=100, null=True, blank=True,
                )),
                # Extra entity add-ons
                ("AdditionalEntities", models.PositiveSmallIntegerField(
                    default=0,
                    help_text=(
                        "Number of entity add-ons purchased beyond plan MaxEntities. "
                        "Billed as Stripe SubscriptionItem quantity."
                    )
                )),
                ("DiscountCode", models.CharField(
                    max_length=50, null=True, blank=True,
                    help_text="Internal discount code applied (e.g. 'nonprofit_50'). For reporting only."
                )),
                ("CreatedAt", models.DateTimeField(auto_now_add=True)),
                ("UpdatedAt", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "entity_subscriptions"},
        ),
        migrations.AddIndex(
            model_name="EntitySubscriptions",
            index=models.Index(
                fields=["StripeCustomerId"],
                name="idx_sub_stripe_customer"
            ),
        ),
        migrations.AddIndex(
            model_name="EntitySubscriptions",
            index=models.Index(
                fields=["StripeSubscriptionId"],
                name="idx_sub_stripe_subscription"
            ),
        ),

        # ── UsageTracking ─────────────────────────────────────────────────────
        migrations.CreateModel(
            name="UsageTracking",
            fields=[
                ("UsageId", models.AutoField(primary_key=True)),
                ("EntityId", models.ForeignKey(
                    "entities.Entities",
                    on_delete=models.CASCADE,
                    related_name="usage_tracking",
                )),
                ("PeriodStart", models.DateField(
                    help_text="Start of the tracked billing period (1st of month for monthly plans)."
                )),
                ("PeriodEnd", models.DateField()),
                # Current usage counters — updated on create/delete of relevant objects
                ("ActiveUsersCount", models.PositiveSmallIntegerField(
                    default=0,
                    help_text="Number of non-deleted, active Users for this entity."
                )),
                ("ReportingYearsCount", models.PositiveSmallIntegerField(
                    default=0,
                    help_text="Number of distinct ReportingYear values in EmissionsData for this entity."
                )),
                ("ApiCallsToday", models.PositiveIntegerField(
                    default=0,
                    help_text="API calls made today (UTC). Reset to 0 at midnight UTC by Celery task."
                )),
                ("ApiCallsMonth", models.PositiveIntegerField(
                    default=0,
                    help_text="Total API calls this billing period."
                )),
                ("TotalEmissionsRecords", models.PositiveIntegerField(
                    default=0,
                    help_text="Count of EmissionsData records for this entity (informational)."
                )),
                ("UpdatedAt", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "usage_tracking"},
        ),
        migrations.AddConstraint(
            model_name="UsageTracking",
            constraint=models.UniqueConstraint(
                fields=["EntityId", "PeriodStart"],
                name="unique_usage_per_entity_period"
            ),
        ),

        # ── Seed data ─────────────────────────────────────────────────────────
        migrations.RunPython(
            seed_plans_and_features,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            seed_free_subscriptions,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
