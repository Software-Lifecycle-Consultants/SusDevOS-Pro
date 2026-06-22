"""
Management command: seed_plans

Seeds the 5 plan definitions and their feature gates. Safe to run multiple times.

Usage:
    python manage.py seed_plans
"""
from django.core.management.base import BaseCommand

PLANS = [
    {"PlanKey": "free",         "PlanName": "Free",         "PriceMonthlyGBP": 0,    "PriceAnnualGBP": 0,     "MaxEntities": 1,  "MaxUsersPerEntity": 1,  "MaxReportingYears": 1, "MaxApiCallsPerDay": 0,    "SupportTier": "docs",          "IsPublic": True,  "SortOrder": 1},
    {"PlanKey": "starter",      "PlanName": "Starter",      "PriceMonthlyGBP": 49,   "PriceAnnualGBP": 470,   "MaxEntities": 1,  "MaxUsersPerEntity": 5,  "MaxReportingYears": 3, "MaxApiCallsPerDay": 0,    "SupportTier": "email_48h",     "IsPublic": True,  "SortOrder": 2},
    {"PlanKey": "professional", "PlanName": "Professional", "PriceMonthlyGBP": 199,  "PriceAnnualGBP": 1908,  "MaxEntities": 5,  "MaxUsersPerEntity": 20, "MaxReportingYears": 0, "MaxApiCallsPerDay": 500,  "SupportTier": "email_24h",     "IsPublic": True,  "SortOrder": 3},
    {"PlanKey": "agency",       "PlanName": "Agency",       "PriceMonthlyGBP": 499,  "PriceAnnualGBP": 4788,  "MaxEntities": 25, "MaxUsersPerEntity": 0,  "MaxReportingYears": 0, "MaxApiCallsPerDay": 2000, "SupportTier": "priority_8h",   "IsPublic": True,  "SortOrder": 4},
    {"PlanKey": "enterprise",   "PlanName": "Enterprise",   "PriceMonthlyGBP": 0,    "PriceAnnualGBP": 0,     "MaxEntities": 0,  "MaxUsersPerEntity": 0,  "MaxReportingYears": 0, "MaxApiCallsPerDay": 0,    "SupportTier": "dedicated_csm", "IsPublic": False, "SortOrder": 5},
]

# (feature_key, upgrade_message, [plans_that_include_it])
FEATURE_GATES = [
    ("scope_1",                    "Scope 1 is available on all plans.",                            ["free","starter","professional","agency","enterprise"]),
    ("scope_2_location_based",     "Location-based Scope 2 is available on all plans.",             ["free","starter","professional","agency","enterprise"]),
    ("scope_2_market_based",       "Market-based Scope 2 requires Starter.",                        ["starter","professional","agency","enterprise"]),
    ("scope_3",                    "Scope 3 supply chain emissions require Starter.",                ["starter","professional","agency","enterprise"]),
    ("scope_3_relevance_assessment","Scope 3 relevance assessments require Starter.",               ["starter","professional","agency","enterprise"]),
    ("ef_library_defra",           "DEFRA emission factors are on all plans.",                      ["free","starter","professional","agency","enterprise"]),
    ("ef_library_full",            "Full emission factor library requires Starter.",                 ["starter","professional","agency","enterprise"]),
    ("ef_auto_update",             "Automatic EF updates require Starter.",                         ["starter","professional","agency","enterprise"]),
    ("ghg_inventory_formal",       "Formal GHG inventories require Starter.",                       ["starter","professional","agency","enterprise"]),
    ("gwp_dataset_selection",      "GWP dataset selection requires Starter.",                       ["starter","professional","agency","enterprise"]),
    ("sbti_targets",               "SBTi target tracking requires Starter.",                        ["starter","professional","agency","enterprise"]),
    ("sbti_registry_sync",         "Automatic SBTi sync requires Professional.",                    ["professional","agency","enterprise"]),
    ("ecosystem_basic",            "Ecosystem tracking requires Starter.",                          ["starter","professional","agency","enterprise"]),
    ("ipcc_biomass_tier1",         "IPCC Tier 1 biomass calculations require Starter.",             ["starter","professional","agency","enterprise"]),
    ("ipcc_biomass_tier2_tier3",   "IPCC Tier 2/3 biomass requires Professional.",                  ["professional","agency","enterprise"]),
    ("land_parcel_gis",            "GIS land parcel mapping requires Professional.",                ["professional","agency","enterprise"]),
    ("tnfd_reporting",             "TNFD-aligned reporting requires Professional.",                  ["professional","agency","enterprise"]),
    ("carbon_offsets",             "Carbon offset management requires Starter.",                    ["starter","professional","agency","enterprise"]),
    ("offset_registry_validation", "Registry validation requires Professional.",                    ["professional","agency","enterprise"]),
    ("companies_house_lookup",     "Companies House auto-populate requires Starter.",               ["starter","professional","agency","enterprise"]),
    ("fx_conversion",              "FX conversion for spend-based Scope 3 requires Starter.",       ["starter","professional","agency","enterprise"]),
    ("report_pdf_watermarked",     "Watermarked PDF reports on Free plan.",                         ["free"]),
    ("report_pdf_unbranded",       "Unbranded PDFs require Starter.",                              ["starter","professional"]),
    ("report_pdf_white_label",     "White-label PDFs require Agency.",                             ["agency","enterprise"]),
    ("report_csv_json_export",     "CSV/JSON export requires Starter.",                            ["starter","professional","agency","enterprise"]),
    ("report_cdp_export",          "CDP-format export requires Professional.",                      ["professional","agency","enterprise"]),
    ("audit_log_30d",              "30-day audit log on all plans.",                               ["free","starter"]),
    ("audit_log_1yr",              "1-year audit log requires Professional.",                       ["professional","agency"]),
    ("audit_log_7yr",              "7-year audit log requires Enterprise.",                        ["enterprise"]),
    ("api_access",                 "API access requires Professional.",                            ["professional","agency","enterprise"]),
    ("client_portal",              "Client read-only portal requires Agency.",                      ["agency","enterprise"]),
    ("white_label_branding",       "White-label branding requires Agency.",                        ["agency","enterprise"]),
    ("bulk_data_import",           "Bulk CSV import requires Professional.",                        ["professional","agency","enterprise"]),
    ("multi_entity_dashboard",     "Multi-entity dashboard requires Professional.",                 ["professional","agency","enterprise"]),
    ("user_privilege_overrides",   "Per-user privilege overrides require Professional.",            ["professional","agency","enterprise"]),
    ("sso_saml",                   "SSO/SAML requires Enterprise.",                               ["enterprise"]),
    ("dedicated_instance",         "Dedicated instance requires Enterprise.",                      ["enterprise"]),
]


class Command(BaseCommand):
    help = "Seed billing Plans and PlanFeatures from spec/pricing.md"

    def handle(self, *args, **options):
        from apps.billing.models import PlanFeatures, Plans

        plan_objects = {}
        for p in PLANS:
            obj, created = Plans.objects.update_or_create(
                PlanKey=p["PlanKey"], defaults=p
            )
            plan_objects[p["PlanKey"]] = obj
            verb = "Created" if created else "Updated"
            self.stdout.write(f"  {verb} plan: {p['PlanName']}")

        added = 0
        for feature_key, upgrade_msg, plan_keys in FEATURE_GATES:
            for plan_key in plan_keys:
                plan = plan_objects.get(plan_key)
                if not plan:
                    continue
                _, created = PlanFeatures.objects.get_or_create(
                    PlanId=plan, FeatureKey=feature_key,
                    defaults={"IsEnabled": True, "UpgradeMessage": upgrade_msg},
                )
                if created:
                    added += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {added} new PlanFeature rows added."
        ))
