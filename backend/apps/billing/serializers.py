from rest_framework import serializers

from .models import EntitySubscriptions, FoundingPartnerApplication, PlanFeatures, Plans


class PlanFeaturesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanFeatures
        fields = ("FeatureKey", "IsEnabled", "LimitValue", "UpgradeMessage")


class PlansSerializer(serializers.ModelSerializer):
    features = PlanFeaturesSerializer(many=True, read_only=True)

    class Meta:
        model = Plans
        fields = ("PlanId", "PlanKey", "PlanName",
                  "PriceMonthlyGBP", "PriceAnnualGBP",
                  "MaxEntities", "MaxUsersPerEntity", "MaxReportingYears",
                  "MaxApiCallsPerDay", "SupportTier", "IsPublic", "SortOrder",
                  "features")


class EntitySubscriptionsSerializer(serializers.ModelSerializer):
    plan = PlansSerializer(source="PlanId", read_only=True)

    class Meta:
        model = EntitySubscriptions
        fields = ("SubscriptionId", "Status", "BillingInterval",
                  "TrialEndsAt", "CurrentPeriodStart", "CurrentPeriodEnd",
                  "CancelAtPeriodEnd", "AdditionalEntities",
                  "StripeCustomerId", "plan")
        read_only_fields = ("SubscriptionId", "StripeCustomerId",
                            "CurrentPeriodStart", "CurrentPeriodEnd")


class FoundingPartnerApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoundingPartnerApplication
        fields = (
            "ApplicationId", "FullName", "Email", "CompanyName", "Role",
            "Website", "UseCase", "LiveProject", "ExpectedUsers",
            "CurrentTooling", "Message", "ConsentToFollowUp", "CreatedAt",
        )
        read_only_fields = ("ApplicationId", "CreatedAt")

    def validate_Email(self, value):  # noqa: N802 — DRF requires the exact model field name
        return value.strip().lower()

    def validate_ExpectedUsers(self, value):  # noqa: N802 — DRF requires the exact model field name
        if value < 1 or value > 10:
            raise serializers.ValidationError("The Founding 10 offer supports 1 to 10 users.")
        return value

    def validate_ConsentToFollowUp(self, value):  # noqa: N802 — DRF requires the exact model field name
        if not value:
            raise serializers.ValidationError("Consent is required so we can review your application.")
        return value
