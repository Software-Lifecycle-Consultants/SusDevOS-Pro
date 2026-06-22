from django.contrib import admin
from .models import Plans, PlanFeatures, EntitySubscriptions, UsageTracking

class PlanFeaturesInline(admin.TabularInline):
    model = PlanFeatures
    extra = 0
    fields = ("FeatureKey", "IsEnabled", "LimitValue")

@admin.register(Plans)
class PlansAdmin(admin.ModelAdmin):
    list_display = ("PlanId", "PlanName", "PlanKey", "PriceMonthlyGBP", "MaxEntities", "IsPublic", "SortOrder")
    list_filter = ("IsPublic",)
    inlines = [PlanFeaturesInline]

@admin.register(EntitySubscriptions)
class EntitySubscriptionsAdmin(admin.ModelAdmin):
    list_display = ("SubscriptionId", "EntityId", "PlanId", "Status", "BillingInterval", "CurrentPeriodEnd")
    list_filter = ("Status", "BillingInterval")
    raw_id_fields = ("EntityId",)
    readonly_fields = ("CreatedAt", "UpdatedAt")
    search_fields = ("StripeCustomerId", "StripeSubscriptionId")

@admin.register(UsageTracking)
class UsageTrackingAdmin(admin.ModelAdmin):
    list_display = ("UsageId", "EntityId", "PeriodStart", "ActiveUsersCount", "ApiCallsToday")
    raw_id_fields = ("EntityId",)

admin.site.register(PlanFeatures)
