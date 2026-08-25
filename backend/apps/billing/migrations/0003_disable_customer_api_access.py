from django.db import migrations

RETIRED_FEATURE = "api_access"
RETIRED_INTERFACE = "manage_entity_api_keys"
PREVIOUS_API_LIMITS = {
    "professional": 500,
    "agency": 2000,
    "enterprise": 0,
}


def disable_customer_api_access(apps, schema_editor):
    Plans = apps.get_model("billing", "Plans")
    PlanFeatures = apps.get_model("billing", "PlanFeatures")
    EntityApiKeys = apps.get_model("shared", "EntityApiKeys")
    Interfaces = apps.get_model("users", "Interfaces")

    Plans.objects.update(MaxApiCallsPerDay=0)
    PlanFeatures.objects.filter(FeatureKey=RETIRED_FEATURE).delete()
    EntityApiKeys.objects.exclude(Status=4).update(Status=4)
    Interfaces.objects.filter(InterfaceKey=RETIRED_INTERFACE, Status=1).update(Status=4)


def restore_plan_configuration_only(apps, schema_editor):
    """Restore plan metadata, but never reactivate previously issued keys."""
    Plans = apps.get_model("billing", "Plans")
    PlanFeatures = apps.get_model("billing", "PlanFeatures")
    for plan_key, api_limit in PREVIOUS_API_LIMITS.items():
        try:
            plan = Plans.objects.get(PlanKey=plan_key)
        except Plans.DoesNotExist:
            continue
        plan.MaxApiCallsPerDay = api_limit
        plan.save(update_fields=["MaxApiCallsPerDay"])
        PlanFeatures.objects.update_or_create(
            PlanId=plan,
            FeatureKey=RETIRED_FEATURE,
            defaults={
                "IsEnabled": True,
                "UpgradeMessage": "API access requires Professional.",
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0002_alter_plans_options"),
        ("shared", "0003_alter_auditlog_logid_alter_auditlog_retentiontier_and_more"),
        ("users", "0003_alter_interfaces_options_alter_modules_options_and_more"),
    ]

    operations = [
        migrations.RunPython(
            disable_customer_api_access,
            restore_plan_configuration_only,
        ),
    ]
