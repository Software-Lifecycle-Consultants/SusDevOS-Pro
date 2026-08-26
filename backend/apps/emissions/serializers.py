from rest_framework import serializers

from apps.shared.serializers import (
    RejectServerManagedInputMixin,
    RejectUnknownFieldsMixin,
    TenantOwnedRelationshipsMixin,
)

from .models import (
    EmissionFactors,
    EmissionFactorSets,
    EmissionsData,
    EmissionsDetails,
    EmissionsOffsets,
    GHGInventories,
    GwpDatasets,
    GwpValues,
    TargetMilestones,
    Targets,
)


class EmissionFactorSetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionFactorSets
        fields = (
            "SetId",
            "SetName",
            "Publisher",
            "Version",
            "ApplicableYear",
            "GeographicScope",
            "IsActive",
        )


class EmissionFactorsSerializer(serializers.ModelSerializer):
    unit = serializers.SerializerMethodField()
    set_name = serializers.SerializerMethodField()
    set_publisher = serializers.SerializerMethodField()

    class Meta:
        model = EmissionFactors
        fields = (
            "FactorId",
            "SetId",
            "set_name",
            "set_publisher",
            "ActivityName",
            "ActivityCategory",
            "Scope",
            "Scope3Category",
            "Gas",
            "GasSubtype",
            "FactorValue",
            "unit",
            "CountryCode",
            "ApplicableYear",
        )

    def get_unit(self, obj):
        return obj.InputUnitId.UnitName if obj.InputUnitId_id else None

    def get_set_name(self, obj):
        return obj.SetId.SetName if obj.SetId_id else None

    def get_set_publisher(self, obj):
        return obj.SetId.Publisher if obj.SetId_id else None


# Fields the server always computes — never writable from client
CALCULATED_FIELDS = (
    "EmissionsAmount",
    "EmissionsAmountTonnes",
    "EmissionsAmountLocationBased",
    "EmissionsAmountMarketBased",
    "EmissionsReduced",
    "EmissionsReducedTonnes",
    "BiogenicCO2AmountTonnes",
    "SpendAmountUSD",
    "ExchangeRateToUSD",
    "ExchangeRateDate",
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
        fields = (
            "GwpDatasetId",
            "Name",
            "Version",
            "Horizon",
            "IsDefault",
            "PublishedYear",
            "gwp_values",
        )


class EmissionsDataListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionsData
        fields = (
            "EmissionsId",
            "Title",
            "Scope",
            "Scope3Category",
            "Gas",
            "EmissionsAmountTonnes",
            "VerificationStatus",
            "ProjectId",
            "PhaseId",
            "InventoryId",
            "ReportingPeriodFrom",
            "ReportingPeriodTo",
            "ReportingYear",
            "Status",
        )


class EmissionsDataSerializer(
    RejectUnknownFieldsMixin,
    TenantOwnedRelationshipsMixin,
    serializers.ModelSerializer,
):
    GwpDatasetId = serializers.PrimaryKeyRelatedField(
        queryset=GwpDatasets.objects.filter(Status=1),
        required=False,
    )
    tenant_owned_relationships = {
        "ProjectId": "EntityId_id",
        "PhaseId": "EntityId_id",
        "InventoryId": "EntityId_id",
    }

    class Meta:
        model = EmissionsData
        fields = "__all__"
        read_only_fields = (
            "EmissionsId",
            "EntityId",
            "CreatedAt",
            "UpdatedAt",
            "CreatedBy",
            "UpdatedBy",
            "VerifiedBy",
            "VerifiedAt",
        ) + CALCULATED_FIELDS

    def validate(self, data):
        # Strip any client-submitted calculated values — rule #1 from CLAUDE.md
        for field in CALCULATED_FIELDS:
            data.pop(field, None)
        data = super().validate(data)

        instance = self.instance
        period_from = data.get(
            "ReportingPeriodFrom",
            getattr(instance, "ReportingPeriodFrom", None),
        )
        period_to = data.get(
            "ReportingPeriodTo",
            getattr(instance, "ReportingPeriodTo", None),
        )
        reporting_year = data.get(
            "ReportingYear",
            getattr(instance, "ReportingYear", None),
        )
        project = data.get(
            "ProjectId",
            getattr(instance, "ProjectId", None),
        )
        phase = data.get(
            "PhaseId",
            getattr(instance, "PhaseId", None),
        )
        inventory = data.get(
            "InventoryId",
            getattr(instance, "InventoryId", None),
        )
        gwp_dataset = data.get(
            "GwpDatasetId",
            getattr(instance, "GwpDatasetId", None),
        )

        errors = {}
        if bool(period_from) != bool(period_to):
            missing = "ReportingPeriodTo" if period_from else "ReportingPeriodFrom"
            errors[missing] = "Both reporting-period dates are required when either is supplied."
        elif period_from and period_to:
            if period_from > period_to:
                errors["ReportingPeriodTo"] = "Reporting period end must be on or after its start."
            if reporting_year and reporting_year != period_to.year:
                errors["ReportingYear"] = "Reporting year must match the period end year."

        if phase is not None:
            if project is None:
                errors["ProjectId"] = "A project is required when a project phase is selected."
            elif phase.ProjectId_id != project.ProjectId:
                errors["PhaseId"] = "The selected phase does not belong to the selected project."

        if inventory is not None:
            if not period_from or not period_to:
                errors["ReportingPeriodFrom"] = (
                    "Reporting-period dates are required for an inventory-assigned record."
                )
            elif (
                period_from < inventory.ReportingPeriodFrom
                or period_to > inventory.ReportingPeriodTo
            ):
                errors["InventoryId"] = (
                    "The record's reporting period must fall within the selected inventory period."
                )
            if reporting_year != inventory.ReportingYear:
                errors["ReportingYear"] = (
                    "Reporting year must match the selected inventory's reporting year."
                )
            if "GwpDatasetId" in data and gwp_dataset != inventory.GwpDatasetId:
                errors["GwpDatasetId"] = (
                    "GWP dataset must match the selected inventory's recorded dataset."
                )
            else:
                # Inventory membership fixes the calculation provenance.  Use
                # that dataset instead of whichever global default is current.
                data["GwpDatasetId"] = inventory.GwpDatasetId
        if errors:
            raise serializers.ValidationError(errors)
        return data


class EmissionsDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionsDetails
        fields = "__all__"
        read_only_fields = (
            "DetailId",
            "EntityId",
            "EmissionsId",
            "EmissionsAmount",
            "EmissionsAmountTonnes",
            "CreatedAt",
            "UpdatedAt",
        )


REGISTRY_RESULT_FIELDS = (
    "RegistryValidatedAt",
    "RegistryValidationStatus",
    "RegistryProjectName",
    "RegistryProjectType",
    "RegistryVintageYear",
    "RegistryRetirementBeneficiary",
)

REGISTRY_IDENTITY_FIELDS = (
    "CreditSerialNumber",
    "CertificateNumber",
    "CreditRegistry",
    "OffsetAmountTonnes",
    "ValidFrom",
    "ValidTo",
)


class EmissionsOffsetsSerializer(RejectServerManagedInputMixin, serializers.ModelSerializer):
    server_managed_input_fields = REGISTRY_RESULT_FIELDS

    class Meta:
        model = EmissionsOffsets
        fields = "__all__"
        read_only_fields = (
            "OffsetId",
            "EntityId",
            "EmissionsId",
            "CreatedAt",
            "UpdatedAt",
        ) + REGISTRY_RESULT_FIELDS

    def update(self, instance, validated_data):
        identity_changed = any(
            field in validated_data and validated_data[field] != getattr(instance, field)
            for field in REGISTRY_IDENTITY_FIELDS
        )
        if identity_changed:
            validated_data.update(
                {
                    "RegistryValidatedAt": None,
                    "RegistryValidationStatus": "unverified",
                    "RegistryProjectName": None,
                    "RegistryProjectType": None,
                    "RegistryVintageYear": None,
                    "RegistryRetirementBeneficiary": None,
                }
            )
        return super().update(instance, validated_data)


class StandaloneEmissionsOffsetsSerializer(
    TenantOwnedRelationshipsMixin,
    EmissionsOffsetsSerializer,
):
    """Offset serializer whose parent emission is selected in the body."""

    EmissionsId = serializers.PrimaryKeyRelatedField(queryset=EmissionsData.objects.all())
    tenant_owned_relationships = {"EmissionsId": "EntityId_id"}

    class Meta(EmissionsOffsetsSerializer.Meta):
        read_only_fields = tuple(
            field
            for field in EmissionsOffsetsSerializer.Meta.read_only_fields
            if field != "EmissionsId"
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if (
            self.instance is not None
            and "EmissionsId" in attrs
            and attrs["EmissionsId"] != self.instance.EmissionsId
        ):
            raise serializers.ValidationError(
                {"EmissionsId": "An offset cannot be moved to another emissions record."}
            )
        return attrs


INVENTORY_SERVER_MANAGED_FIELDS = (
    "VerificationStatus",
    "VerifiedBy",
    "VerifiedAt",
    "VerificationNotes",
    "TotalScope1Tonnes",
    "TotalScope2LocationTonnes",
    "TotalScope2MarketTonnes",
    "TotalScope3Tonnes",
    "TotalOffsetsTonnes",
    "NetEmissionsTonnes",
    "TotalsLastComputedAt",
)


class GHGInventoriesSerializer(
    RejectUnknownFieldsMixin,
    RejectServerManagedInputMixin,
    serializers.ModelSerializer,
):
    server_managed_input_fields = INVENTORY_SERVER_MANAGED_FIELDS
    GwpDatasetId = serializers.PrimaryKeyRelatedField(
        queryset=GwpDatasets.objects.filter(Status=1),
        required=False,
    )
    GwpDatasetName = serializers.CharField(source="GwpDatasetId.Name", read_only=True)

    class Meta:
        model = GHGInventories
        fields = "__all__"
        read_only_fields = (
            "InventoryId",
            "EntityId",
            "VerifiedBy",
            "VerifiedAt",
            "TotalScope1Tonnes",
            "TotalScope2LocationTonnes",
            "TotalScope2MarketTonnes",
            "TotalScope3Tonnes",
            "TotalOffsetsTonnes",
            "NetEmissionsTonnes",
            "TotalsLastComputedAt",
            "CreatedAt",
            "UpdatedAt",
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = self.instance
        period_from = attrs.get(
            "ReportingPeriodFrom",
            getattr(instance, "ReportingPeriodFrom", None),
        )
        period_to = attrs.get(
            "ReportingPeriodTo",
            getattr(instance, "ReportingPeriodTo", None),
        )
        reporting_year = attrs.get(
            "ReportingYear",
            getattr(instance, "ReportingYear", None),
        )
        baseline_year = attrs.get(
            "BaselineYear",
            getattr(instance, "BaselineYear", None),
        )

        errors = {}
        if period_from and period_to:
            if period_from > period_to:
                errors["ReportingPeriodTo"] = "Reporting period end must be on or after its start."
            elif (period_to - period_from).days > 366:
                errors["ReportingPeriodTo"] = "A formal inventory period cannot exceed 366 days."
            if reporting_year and reporting_year != period_to.year:
                errors["ReportingYear"] = "Reporting year must match the period end year."
        if baseline_year and reporting_year and baseline_year > reporting_year:
            errors["BaselineYear"] = "Baseline year cannot be after the reporting year."
        if instance is not None and instance.emissions_records.filter(Status__lt=4).exists():
            protected_fields = (
                "ReportingYear",
                "ReportingPeriodFrom",
                "ReportingPeriodTo",
                "GwpDatasetId",
            )
            for field in protected_fields:
                if field in attrs and attrs[field] != getattr(instance, field):
                    errors[field] = (
                        "This field cannot change while emissions records are assigned to the inventory."
                    )
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


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
