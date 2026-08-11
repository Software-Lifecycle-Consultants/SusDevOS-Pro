from django.contrib import admin
from .models import (
    GwpDatasets, GwpValues, Units, EmissionFactorSets, EmissionFactors,
    GHGInventories, Scope3RelevanceAssessments, EmissionsData,
    EmissionsDetails, EmissionsOffsets, ExchangeRates, Targets, TargetMilestones,
)

@admin.register(GwpDatasets)
class GwpDatasetsAdmin(admin.ModelAdmin):
    list_display = ("GwpDatasetId", "Name", "Version", "Horizon", "IsDefault", "PublishedYear")
    list_filter = ("IsDefault", "Version")

@admin.register(GwpValues)
class GwpValuesAdmin(admin.ModelAdmin):
    list_display = ("GwpValueId", "GwpDatasetId", "Gas", "GasSubtype", "GwpFactor")
    list_filter = ("GwpDatasetId", "Gas")

@admin.register(Units)
class UnitsAdmin(admin.ModelAdmin):
    list_display = ("UnitId", "UnitName", "UnitSymbol", "PhysicalDimension", "ConversionFactor", "IsCanonical")
    list_filter = ("PhysicalDimension", "IsCanonical")

@admin.register(EmissionFactorSets)
class EmissionFactorSetsAdmin(admin.ModelAdmin):
    list_display = ("SetId", "SetName", "Publisher", "Version", "ApplicableYear", "IsActive")
    list_filter = ("Publisher", "IsActive")

@admin.register(EmissionFactors)
class EmissionFactorsAdmin(admin.ModelAdmin):
    list_display = ("FactorId", "ActivityName", "Scope", "Gas", "FactorValue", "CountryCode", "ApplicableYear")
    list_filter = ("Scope", "Gas", "CountryCode")
    search_fields = ("ActivityName", "ClimatiqActivityId")

@admin.register(GHGInventories)
class GHGInventoriesAdmin(admin.ModelAdmin):
    list_display = ("InventoryId", "EntityId", "ReportingYear", "VerificationStatus", "Status")
    list_filter = ("VerificationStatus", "Status")
    raw_id_fields = ("EntityId",)

@admin.register(EmissionsData)
class EmissionsDataAdmin(admin.ModelAdmin):
    list_display = (
        "EmissionsId", "Title", "EntityId", "Scope", "Gas",
        "EmissionsAmountTonnes", "VerificationStatus", "Status",
    )
    list_filter = ("Scope", "VerificationStatus", "Status", "Gas")
    search_fields = ("Title",)
    raw_id_fields = ("EntityId", "ProjectId")
    # All server-computed fields are read-only in admin too — a staff user must
    # not be able to type over the calculated GHG figures (CLAUDE.md rule #1).
    # Mirrors CALCULATED_FIELDS in serializers.py.
    readonly_fields = (
        "EmissionsAmount", "EmissionsAmountTonnes",
        "EmissionsAmountLocationBased", "EmissionsAmountMarketBased",
        "EmissionsReduced", "EmissionsReducedTonnes",
        "BiogenicCO2AmountTonnes", "SpendAmountUSD",
        "ExchangeRateToUSD", "ExchangeRateDate", "QuantityCanonical",
    )

@admin.register(Targets)
class TargetsAdmin(admin.ModelAdmin):
    list_display = ("TargetId", "TargetName", "EntityId", "TargetType", "BaselineYear", "TargetYear")
    list_filter = ("TargetType", "ValidationStatus")
    raw_id_fields = ("EntityId",)

admin.site.register(Scope3RelevanceAssessments)
admin.site.register(EmissionsDetails)
admin.site.register(EmissionsOffsets)
admin.site.register(ExchangeRates)
admin.site.register(TargetMilestones)
