from importlib import import_module

from django.apps import apps as django_apps
from django.core.management import call_command

import pytest

from apps.billing.models import PlanFeatures, Plans
from apps.shared.models import EntityApiKeys
from apps.users.models import Interfaces, Modules

pytestmark = pytest.mark.django_db


def test_seed_plans_reconciles_retired_api_access():
    call_command("seed_plans", verbosity=0)
    professional = Plans.objects.get(PlanKey="professional")
    professional.MaxApiCallsPerDay = 999
    professional.save(update_fields=["MaxApiCallsPerDay"])
    PlanFeatures.objects.create(
        PlanId=professional,
        FeatureKey="api_access",
        IsEnabled=True,
        UpgradeMessage="stale",
    )

    call_command("seed_plans", verbosity=0)
    call_command("seed_plans", verbosity=0)

    assert not Plans.objects.exclude(MaxApiCallsPerDay=0).exists()
    assert not PlanFeatures.objects.filter(FeatureKey="api_access").exists()


def test_retirement_data_operation_preserves_but_never_reactivates_keys():
    professional = Plans.objects.create(
        PlanKey="professional",
        PlanName="Professional",
        PriceMonthlyGBP=199,
        PriceAnnualGBP=1908,
        MaxEntities=5,
        MaxUsersPerEntity=20,
        MaxReportingYears=0,
        MaxApiCallsPerDay=500,
        SupportTier="email_24h",
    )
    PlanFeatures.objects.create(
        PlanId=professional,
        FeatureKey="api_access",
        IsEnabled=True,
        UpgradeMessage="stale",
    )
    key = EntityApiKeys.objects.create(
        EntityId=123,
        HashedApiKey="a" * 64,
        KeyPrefix="sk_test",
        Status=1,
    )
    module = Modules.objects.create(
        ModuleName="Entity Management",
        ModuleKey="entity_management_retirement_test",
    )
    interface = Interfaces.objects.create(
        ModuleId=module,
        InterfaceName="Manage API Keys",
        InterfaceKey="manage_entity_api_keys",
        Status=1,
    )
    migration = import_module(
        "apps.billing.migrations.0003_disable_customer_api_access"
    )

    migration.disable_customer_api_access(django_apps, None)

    professional.refresh_from_db()
    key.refresh_from_db()
    interface.refresh_from_db()
    assert professional.MaxApiCallsPerDay == 0
    assert not PlanFeatures.objects.filter(FeatureKey="api_access").exists()
    assert key.Status == 4
    assert interface.Status == 4

    migration.restore_plan_configuration_only(django_apps, None)

    professional.refresh_from_db()
    key.refresh_from_db()
    interface.refresh_from_db()
    assert professional.MaxApiCallsPerDay == 500
    assert PlanFeatures.objects.filter(
        PlanId=professional,
        FeatureKey="api_access",
        IsEnabled=True,
    ).exists()
    assert interface.Status == 4
    assert key.Status == 4
