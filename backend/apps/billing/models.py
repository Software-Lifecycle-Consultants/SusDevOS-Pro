"""Billing app models. Ref: reference migration 0028_plans_subscriptions."""
from django.db import models


class Plans(models.Model):
    PlanId = models.AutoField(primary_key=True)
    PlanKey = models.CharField(max_length=50, unique=True)
    PlanName = models.CharField(max_length=100)
    PriceMonthlyGBP = models.PositiveIntegerField()
    PriceAnnualGBP = models.PositiveIntegerField()
    MaxEntities = models.PositiveSmallIntegerField(help_text="0 = unlimited")
    MaxUsersPerEntity = models.PositiveSmallIntegerField(help_text="0 = unlimited")
    MaxReportingYears = models.PositiveSmallIntegerField(help_text="0 = unlimited; 1 = current year only")
    MaxApiCallsPerDay = models.PositiveIntegerField(default=0, help_text="0 = no API access")
    AdditionalEntityPriceGBP = models.PositiveIntegerField(default=0)
    SupportTier = models.CharField(max_length=50)
    IsPublic = models.BooleanField(default=True)
    SortOrder = models.PositiveSmallIntegerField(default=0)
    StripePriceIdMonthly = models.CharField(max_length=100, blank=True)
    StripePriceIdAnnual = models.CharField(max_length=100, blank=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "plans"
        ordering = ["SortOrder"]

    def __str__(self):
        return self.PlanName


class PlanFeatures(models.Model):
    PlanFeatureId = models.AutoField(primary_key=True)
    PlanId = models.ForeignKey(Plans, on_delete=models.CASCADE, related_name="features")
    FeatureKey = models.CharField(max_length=100)
    IsEnabled = models.BooleanField(default=True)
    LimitValue = models.PositiveIntegerField(null=True, blank=True)
    UpgradeMessage = models.TextField()

    class Meta:
        db_table = "plan_features"
        constraints = [
            models.UniqueConstraint(fields=["PlanId", "FeatureKey"], name="unique_feature_per_plan")
        ]
        indexes = [models.Index(fields=["PlanId", "FeatureKey"], name="idx_plan_feature_key")]

    def __str__(self):
        return f"{self.PlanId}: {self.FeatureKey}"


class EntitySubscriptions(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"), ("trialing", "Trial"), ("past_due", "Past Due"),
        ("canceled", "Canceled"), ("incomplete", "Incomplete"),
    ]
    INTERVAL_CHOICES = [("monthly", "Monthly"), ("annual", "Annual")]

    SubscriptionId = models.AutoField(primary_key=True)
    EntityId = models.OneToOneField(
        "entities.Entities", on_delete=models.PROTECT, related_name="subscription"
    )
    PlanId = models.ForeignKey(Plans, on_delete=models.PROTECT, related_name="subscriptions")
    Status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    BillingInterval = models.CharField(max_length=10, choices=INTERVAL_CHOICES, default="monthly")
    TrialEndsAt = models.DateTimeField(null=True, blank=True)
    CurrentPeriodStart = models.DateTimeField(null=True, blank=True)
    CurrentPeriodEnd = models.DateTimeField(null=True, blank=True)
    CanceledAt = models.DateTimeField(null=True, blank=True)
    CancelAtPeriodEnd = models.BooleanField(default=False)
    StripeCustomerId = models.CharField(max_length=100, blank=True)
    StripeSubscriptionId = models.CharField(max_length=100, blank=True)
    StripeLatestInvoiceId = models.CharField(max_length=100, blank=True)
    AdditionalEntities = models.PositiveSmallIntegerField(default=0)
    DiscountCode = models.CharField(max_length=50, blank=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "entity_subscriptions"
        indexes = [
            models.Index(fields=["StripeCustomerId"], name="idx_sub_stripe_customer"),
            models.Index(fields=["StripeSubscriptionId"], name="idx_sub_stripe_subscription"),
        ]

    def __str__(self):
        return f"{self.EntityId} - {self.PlanId} ({self.Status})"


class UsageTracking(models.Model):
    UsageId = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.CASCADE, related_name="usage_tracking")
    PeriodStart = models.DateField()
    PeriodEnd = models.DateField()
    ActiveUsersCount = models.PositiveSmallIntegerField(default=0)
    ReportingYearsCount = models.PositiveSmallIntegerField(default=0)
    ApiCallsToday = models.PositiveIntegerField(default=0)
    ApiCallsMonth = models.PositiveIntegerField(default=0)
    TotalEmissionsRecords = models.PositiveIntegerField(default=0)
    UpdatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "usage_tracking"
        constraints = [
            models.UniqueConstraint(
                fields=["EntityId", "PeriodStart"], name="unique_usage_per_entity_period"
            )
        ]

    def __str__(self):
        return f"{self.EntityId} usage {self.PeriodStart} to {self.PeriodEnd}"
