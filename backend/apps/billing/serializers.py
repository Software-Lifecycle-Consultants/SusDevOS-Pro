from rest_framework import serializers

from .models import EntitySubscriptions, PlanFeatures, Plans


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
