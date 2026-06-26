from rest_framework import serializers
from .models import (
    EmissionFactorSets, EmissionFactors,
    EmissionsData, EmissionsDetails, EmissionsOffsets,
    GwpDatasets, GwpValues, GHGInventories, Targets, TargetMilestones,
)


class EmissionFactorSetsSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EmissionFactorSets
        fields = (
            "SetId", "SetName", "Publisher", "Version",
            "ApplicableYear", "GeographicScope", "IsActive",
        )


class EmissionFactorsSerializer(serializers.ModelSerializer):
    unit          = serializers.SerializerMethodField()
    set_name      = serializers.SerializerMethodField()
    set_publisher = serializers.SerializerMethodField()

    class Meta:
        model  = EmissionFactors
        fields = (
            "FactorId", "SetId", "set_name", "set_publisher",
            "ActivityName", "ActivityCategory",
            "Scope", "Scope3Category",
            "Gas", "GasSubtype",
            "FactorValue", "unit",
            "CountryCode", "ApplicableYear",
        )

    def get_unit(self, obj):
        return obj.InputUnitId.UnitName if obj.InputUnitId_id else None

    def get_set_name(self, obj):
        return obj.SetId.SetName if obj.SetId_id else None

    def get_set_publisher(self, obj):
        return obj.SetId.Publisher if obj.SetId_id else None

# Fields the server always computes — never writable from client
CALCULATED_FIELDS = (
    "EmissionsAmount", "EmissionsAmountTonnes",
    "EmissionsAmountLocationBased", "EmissionsAmountMarketBased",
    "EmissionsReduced", "EmissionsReducedTonnes",
    "BiogenicCO2AmountTonnes",
    "SpendAmountUSD", "ExchangeRateToUSD", "ExchangeRateDate",
    "QuantityCanonical",
)


class GwpValuesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GwpValues
        fields = ("GwpValueId", "Gas", "GasSubtype", "GwpFactor")


class GwpDatasetsSerializer(serializers.ModelSerializer):
    gwp_values = GwpValuesSerializer(many=True, read_only=True)

    class Meta:
        model = GwpDatasets
        fields = ("GwpDatasetId", "Name", "Version", "Horizon", "IsDefault",
                  "PublishedYear", "gwp_values")


class EmissionsDataListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionsData
        fields = (
            "EmissionsId", "Title", "Scope", "Scope3Category",
            "Gas", "EmissionsAmountTonnes", "VerificationStatus",
            "ProjectId", "ReportingYear", "Status",
        )


class EmissionsDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionsData
        fields = "__all__"
        read_only_fields = (
            ("EmissionsId", "EntityId", "CreatedAt", "UpdatedAt", "CreatedBy", "UpdatedBy",
             "VerifiedBy", "VerifiedAt") + CALCULATED_FIELDS
        )

    def validate(self, data):
        # Strip any client-submitted calculated values — rule #1 from CLAUDE.md
        for field in CALCULATED_FIELDS:
            data.pop(field, None)
        return data


class EmissionsDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionsDetails
        fields = "__all__"
        read_only_fields = ("DetailId", "EntityId", "EmissionsAmount",
                            "EmissionsAmountTonnes", "CreatedAt", "UpdatedAt")


class EmissionsOffsetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionsOffsets
        fields = "__all__"
        read_only_fields = ("OffsetId", "EntityId", "CreatedAt", "UpdatedAt")


class GHGInventoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GHGInventories
        fields = "__all__"
        read_only_fields = (
            "InventoryId", "EntityId", "VerifiedBy", "VerifiedAt",
            "TotalScope1Tonnes", "TotalScope2LocationTonnes",
            "TotalScope2MarketTonnes", "TotalScope3Tonnes",
            "TotalOffsetsTonnes", "NetEmissionsTonnes",
            "CreatedAt", "UpdatedAt",
        )


class TargetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Targets
        fields = "__all__"
        read_only_fields = ("TargetId", "EntityId", "CreatedAt", "UpdatedAt")


class TargetMilestonesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TargetMilestones
        fields = "__all__"
        read_only_fields = ("MilestoneId", "EntityId", "CreatedAt", "UpdatedAt")
