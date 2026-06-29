"""
Emissions app models.

GHG Protocol Corporate Standard. All calculation logic lives in
EmissionsData.save() -- client-submitted EmissionsAmount is always overwritten.

Critical rules (CLAUDE.md):
  1. Never compute emissions on the client.
  2. Biogenic CO2 goes in BiogenicCO2AmountTonnes, NOT the GWP total.
  3. Scope 2 requires both location-based and market-based methods.
  4. VerificationStatus >= 3 -> immutable (enforced in serializer).
"""
from django.db import models

from apps.shared.models import BaseAuditMixin

REGISTRY_VALIDATION_STATUS = [
    ("pending", "Pending"), ("valid", "Valid"),
    ("invalid", "Invalid"), ("unverified", "Unverified"),
]

CONSOLIDATION_APPROACH_CHOICES = [
    (1, "Equity Share"), (2, "Financial Control"), (3, "Operational Control"),
]


class GwpDatasets(BaseAuditMixin):
    GwpDatasetId = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=100)
    Version = models.CharField(max_length=20)
    Horizon = models.PositiveSmallIntegerField(help_text="GWP time horizon: 20 or 100")
    IsDefault = models.BooleanField(default=False)
    PublishedYear = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "gwp_datasets"
        ordering = ["-PublishedYear"]

    def __str__(self):
        return self.Name


class GwpValues(BaseAuditMixin):
    GwpValueId = models.AutoField(primary_key=True)
    GwpDatasetId = models.ForeignKey(GwpDatasets, on_delete=models.PROTECT, related_name="gwp_values")
    Gas = models.CharField(max_length=50)
    GasSubtype = models.CharField(max_length=50, blank=True, null=True)
    GwpFactor = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        db_table = "gwp_values"
        constraints = [
            models.UniqueConstraint(
                fields=["GwpDatasetId", "Gas", "GasSubtype"], name="unique_gwp_gas_per_dataset"
            )
        ]

    def __str__(self):
        return f"{self.Gas} ({self.GwpDatasetId.Version}): {self.GwpFactor}"


class Units(BaseAuditMixin):
    """Unit conversion reference table. All EFs are expressed per canonical unit."""
    UnitId = models.AutoField(primary_key=True)
    UnitName = models.CharField(max_length=100)
    UnitSymbol = models.CharField(max_length=20)
    PhysicalDimension = models.CharField(max_length=50)
    ConversionFactor = models.DecimalField(max_digits=20, decimal_places=10)
    CanonicalUnit = models.CharField(max_length=20)
    IsCanonical = models.BooleanField(default=False)

    class Meta:
        db_table = "units"
        ordering = ["UnitName"]

    def __str__(self):
        return f"{self.UnitName} ({self.UnitSymbol})"


class EmissionFactorSets(BaseAuditMixin):
    SetId = models.AutoField(primary_key=True)
    SetName = models.CharField(max_length=200)
    Publisher = models.CharField(max_length=200)
    Version = models.CharField(max_length=50, blank=True, null=True)
    ApplicableYear = models.PositiveSmallIntegerField(null=True, blank=True)
    GeographicScope = models.CharField(max_length=100, blank=True, null=True)
    IsActive = models.BooleanField(default=True)

    class Meta:
        db_table = "emission_factor_sets"
        ordering = ["-ApplicableYear", "SetName"]

    def __str__(self):
        return self.SetName


class EmissionFactors(BaseAuditMixin):
    FactorId = models.AutoField(primary_key=True)
    SetId = models.ForeignKey(EmissionFactorSets, on_delete=models.PROTECT, related_name="factors")
    ActivityName = models.CharField(max_length=200)
    ActivityCategory = models.CharField(max_length=200, blank=True, null=True)
    Scope = models.PositiveSmallIntegerField()
    Scope3Category = models.PositiveSmallIntegerField(null=True, blank=True)
    Gas = models.CharField(max_length=50)
    GasSubtype = models.CharField(max_length=50, null=True, blank=True)
    FactorValue = models.DecimalField(max_digits=18, decimal_places=8)
    InputUnitId = models.ForeignKey(Units, on_delete=models.PROTECT, null=True, blank=True, related_name="emission_factors")
    CountryCode = models.CharField(max_length=3, blank=True, null=True)
    ApplicableYear = models.PositiveSmallIntegerField(null=True, blank=True)
    ClimatiqActivityId = models.CharField(max_length=200, null=True, blank=True)
    GridSubregion = models.CharField(max_length=50, null=True, blank=True)
    ExternalSyncedAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "emission_factors"
        ordering = ["ActivityName"]
        indexes = [
            models.Index(fields=["ClimatiqActivityId", "CountryCode", "ApplicableYear"], name="idx_ef_climatiq_key"),
        ]

    def __str__(self):
        return f"{self.ActivityName} ({self.Gas})"


class GHGInventories(BaseAuditMixin):
    """Formal versioned GHG inventory. VerificationStatus >= 3 -> immutable."""
    VERIFICATION_STATUS_CHOICES = [
        (1, "Unverified"), (2, "Pending"), (3, "Verified - First Party"),
        (4, "Verified - Third Party"),
    ]

    InventoryId = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.PROTECT, related_name="ghg_inventories")
    ReportingYear = models.PositiveSmallIntegerField()
    ReportingPeriodFrom = models.DateField()
    ReportingPeriodTo = models.DateField()
    BaselineYear = models.PositiveSmallIntegerField(null=True, blank=True)
    GwpDatasetId = models.ForeignKey(GwpDatasets, on_delete=models.PROTECT, related_name="inventories")
    ConsolidationApproach = models.PositiveSmallIntegerField(
        null=True, blank=True, choices=CONSOLIDATION_APPROACH_CHOICES
    )
    VerificationStatus = models.PositiveSmallIntegerField(default=1, choices=VERIFICATION_STATUS_CHOICES)
    VerifiedBy = models.ForeignKey(
        "users.Users", on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_inventories"
    )
    VerifiedAt = models.DateTimeField(null=True, blank=True)
    VerificationNotes = models.TextField(blank=True, null=True)
    TotalScope1Tonnes = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    TotalScope2LocationTonnes = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    TotalScope2MarketTonnes = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    TotalScope3Tonnes = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    TotalOffsetsTonnes = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    NetEmissionsTonnes = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    TotalsLastComputedAt = models.DateTimeField(
        null=True, blank=True,
        help_text="Timestamp of last scope-total recompute. NULL or >24h old => stale (see tasks.emissions).",
    )

    class Meta:
        db_table = "ghg_inventories"
        ordering = ["-ReportingYear"]
        indexes = [models.Index(fields=["EntityId", "ReportingYear"], name="idx_inventory_entity_year")]

    def __str__(self):
        return f"{self.EntityId} - {self.ReportingYear}"


class Scope3RelevanceAssessments(BaseAuditMixin):
    AssessmentId = models.AutoField(primary_key=True)
    InventoryId = models.ForeignKey(GHGInventories, on_delete=models.CASCADE, related_name="scope3_assessments")
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.PROTECT, related_name="scope3_assessments")
    CategoryNumber = models.PositiveSmallIntegerField()
    IsRelevant = models.BooleanField(null=True, blank=True)
    ExclusionReason = models.TextField(blank=True, null=True)
    Notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "scope3_relevance_assessments"
        constraints = [
            models.UniqueConstraint(
                fields=["InventoryId", "CategoryNumber"],
                name="unique_scope3_category_per_inventory",
            )
        ]


class EmissionsData(BaseAuditMixin):
    """
    Core GHG record. save() triggers server-side calculation.
    Client-submitted EmissionsAmount is ALWAYS overwritten.
    """
    EmissionsId = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.PROTECT, related_name="emissions_records")
    ProjectId = models.ForeignKey(
        "projects.DevelopmentProjects", on_delete=models.SET_NULL, null=True, blank=True, related_name="emissions_records"
    )
    PhaseId = models.ForeignKey(
        "projects.ProjectPhases", on_delete=models.SET_NULL, null=True, blank=True, related_name="emissions_records"
    )
    InventoryId = models.ForeignKey(
        GHGInventories, on_delete=models.SET_NULL, null=True, blank=True, related_name="emissions_records"
    )
    Title = models.CharField(max_length=200)
    Scope = models.PositiveSmallIntegerField()
    Scope3Category = models.PositiveSmallIntegerField(null=True, blank=True)
    ActivityDescription = models.TextField(blank=True, null=True)
    QuantityOrCost = models.DecimalField(max_digits=18, decimal_places=4)
    InputUnitId = models.ForeignKey(
        Units, on_delete=models.PROTECT, null=True, blank=True, related_name="emissions_data"
    )
    Unit = models.CharField(max_length=50)
    QuantityCanonical = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    EmissionFactor = models.DecimalField(max_digits=18, decimal_places=8)
    EmissionFactorSource = models.CharField(max_length=200)
    EmissionFactorId = models.ForeignKey(
        EmissionFactors, on_delete=models.SET_NULL, null=True, blank=True, related_name="emissions_records"
    )
    Gas = models.CharField(max_length=50)
    GasSubtype = models.CharField(max_length=50, null=True, blank=True)
    GwpDatasetId = models.ForeignKey(GwpDatasets, on_delete=models.PROTECT, related_name="emissions_records")
    # Calculated outputs (server-side only)
    EmissionsAmount = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    EmissionsAmountTonnes = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    EmissionsReduced = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    EmissionsReducedTonnes = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    # Biogenic CO2 -- NOT in GWP total (critical rule #4)
    BiogenicCO2FactorKg = models.DecimalField(
        max_digits=18, decimal_places=8, null=True, blank=True,
        help_text="kg biogenic CO2 per canonical unit of fuel (combustion of biomass/biofuels).",
    )
    BiogenicCO2AmountTonnes = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    # Scope 2 dual method (critical rule #5) — separate location/market EF inputs
    EFLocationBased = models.DecimalField(
        max_digits=18, decimal_places=8, null=True, blank=True,
        help_text="Grid-average emission factor (kg CO2e per canonical unit).",
    )
    EFMarketBased = models.DecimalField(
        max_digits=18, decimal_places=8, null=True, blank=True,
        help_text="Contractual/supplier emission factor (kg CO2e per canonical unit); 0 if 100% renewable EACs.",
    )
    EmissionsAmountLocationBased = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    EmissionsAmountMarketBased = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    # Spend-based FX (from 0027)
    SpendCurrency = models.CharField(max_length=3, null=True, blank=True)
    SpendAmountLocal = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    SpendAmountUSD = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    ExchangeRateToUSD = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    ExchangeRateDate = models.DateField(null=True, blank=True)
    GridSubregion = models.CharField(max_length=50, null=True, blank=True)
    BaselineYear = models.PositiveSmallIntegerField(null=True, blank=True)
    ReportingPeriodFrom = models.DateField(null=True, blank=True)
    ReportingPeriodTo = models.DateField(null=True, blank=True)
    ReportingYear = models.PositiveSmallIntegerField(null=True, blank=True)
    VerificationStatus = models.PositiveSmallIntegerField(default=1)
    VerifiedBy = models.ForeignKey(
        "users.Users", on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_emissions"
    )
    VerifiedAt = models.DateTimeField(null=True, blank=True)
    VerificationNotes = models.TextField(null=True, blank=True)
    CountsTowardNDC = models.BooleanField(default=False)

    class Meta:
        db_table = "emissions_data"
        ordering = ["-CreatedAt"]
        indexes = [
            models.Index(fields=["EntityId", "ProjectId"], name="idx_emissions_entity_project"),
            models.Index(fields=["EntityId", "Scope"], name="idx_emissions_entity_scope"),
            models.Index(fields=["VerificationStatus"], name="idx_emissions_verification"),
            models.Index(fields=["ReportingPeriodFrom", "ReportingPeriodTo"], name="idx_emissions_period"),
        ]

    def save(self, *args, **kwargs):
        from apps.emissions.services import compute_emissions
        compute_emissions(self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.Title


class EmissionsDetails(BaseAuditMixin):
    DetailId = models.AutoField(primary_key=True)
    EmissionsId = models.ForeignKey(EmissionsData, on_delete=models.CASCADE, related_name="details")
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.PROTECT, related_name="emissions_details")
    Description = models.CharField(max_length=200)
    QuantityOrCost = models.DecimalField(max_digits=18, decimal_places=4)
    Unit = models.CharField(max_length=50)
    EmissionFactor = models.DecimalField(max_digits=18, decimal_places=8)
    EmissionFactorSource = models.CharField(max_length=200)
    Gas = models.CharField(max_length=50)
    GasSubtype = models.CharField(max_length=50, null=True, blank=True)
    GwpDatasetId = models.ForeignKey(GwpDatasets, on_delete=models.PROTECT, related_name="emissions_details")
    EmissionsAmount = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    EmissionsAmountTonnes = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    Remarks = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "emissions_details"


class EmissionsOffsets(BaseAuditMixin):
    OffsetId = models.AutoField(primary_key=True)
    EmissionsId = models.ForeignKey(EmissionsData, on_delete=models.CASCADE, related_name="offsets")
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.PROTECT, related_name="emissions_offsets")
    Title = models.CharField(max_length=200)
    OffsetType = models.CharField(max_length=100)
    Provider = models.CharField(max_length=200)
    CertificateNumber = models.CharField(max_length=100, blank=True, null=True)
    OffsetAmountTonnes = models.DecimalField(max_digits=18, decimal_places=6)
    ValidFrom = models.DateField(null=True, blank=True)
    ValidTo = models.DateField(null=True, blank=True)
    Remarks = models.TextField(null=True, blank=True)
    CreditSerialNumber = models.CharField(max_length=200, null=True, blank=True)
    RegistryValidatedAt = models.DateTimeField(null=True, blank=True)
    RegistryValidationStatus = models.CharField(
        max_length=20, null=True, blank=True, choices=REGISTRY_VALIDATION_STATUS, default="unverified"
    )
    RegistryProjectName = models.CharField(max_length=300, null=True, blank=True)
    RegistryProjectType = models.CharField(max_length=200, null=True, blank=True)
    RegistryVintageYear = models.PositiveSmallIntegerField(null=True, blank=True)
    RegistryRetirementBeneficiary = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = "emissions_offsets"
        indexes = [models.Index(fields=["CreditSerialNumber"], name="idx_offset_serial_number")]


class ExchangeRates(models.Model):
    RateId = models.AutoField(primary_key=True)
    FromCurrency = models.CharField(max_length=3)
    ToCurrency = models.CharField(max_length=3, default="USD")
    Rate = models.DecimalField(max_digits=18, decimal_places=8)
    RateDate = models.DateField()
    Source = models.CharField(max_length=50)
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "exchange_rates"
        constraints = [
            models.UniqueConstraint(
                fields=["FromCurrency", "ToCurrency", "RateDate"],
                name="unique_fx_rate_per_currency_pair_date",
            )
        ]
        indexes = [models.Index(fields=["FromCurrency", "ToCurrency", "RateDate"], name="idx_fx_currency_date")]


class Targets(BaseAuditMixin):
    TargetId = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.PROTECT, related_name="targets")
    TargetName = models.CharField(max_length=200)
    TargetType = models.CharField(max_length=50)
    BaselineYear = models.PositiveSmallIntegerField()
    TargetYear = models.PositiveSmallIntegerField()
    BaselineEmissionsTonnes = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    ReductionPercent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    Scope = models.PositiveSmallIntegerField(null=True, blank=True)
    ValidationStatus = models.PositiveSmallIntegerField(default=1)
    Notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "targets"
        ordering = ["-TargetYear"]

    def __str__(self):
        return self.TargetName


class TargetMilestones(BaseAuditMixin):
    MilestoneId = models.AutoField(primary_key=True)
    TargetId = models.ForeignKey(Targets, on_delete=models.CASCADE, related_name="milestones")
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.PROTECT, related_name="target_milestones")
    MilestoneYear = models.PositiveSmallIntegerField()
    TargetEmissionsTonnes = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    ActualEmissionsTonnes = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    IsAchieved = models.BooleanField(default=False)
    Notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "target_milestones"
        ordering = ["MilestoneYear"]
