from rest_framework import serializers

from apps.shared.serializers import TenantOwnedRelationshipsMixin

from .models import (
    Restorations,
    RestorationSpecies,
    TreeRemovalAffectedSpecies,
    TreeRemovalRemovedSpecies,
    TreeRemovals,
)


class TreeRemovalsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreeRemovals
        fields = ("TreeRemovalId", "ProjectId", "RemovalDate",
                  "TotalTreesRemoved", "TotalBiomassCarbon", "Status")


class TreeRemovalsDetailSerializer(TenantOwnedRelationshipsMixin, serializers.ModelSerializer):
    tenant_owned_relationships = {"ProjectId": "EntityId_id"}

    class Meta:
        model = TreeRemovals
        fields = "__all__"
        # TotalBiomassCarbon is server-computed (IPCC LULUCF); never trust client values.
        read_only_fields = ("TreeRemovalId", "EntityId", "TotalBiomassCarbon",
                            "CreatedAt", "UpdatedAt", "CreatedBy", "UpdatedBy")


class TreeRemovalSpeciesSerializer(TenantOwnedRelationshipsMixin, serializers.ModelSerializer):
    tenant_owned_relationships = {"SpeciesId": "EntityId_id"}

    class Meta:
        model = TreeRemovalRemovedSpecies
        fields = (
            "id", "SpeciesId", "Count",
            # client inputs
            "VolumeM3", "BiomassCalculationMethod", "BiomassCalculationNotes",
            "DeadOrganicMatterTonnesCO2e", "SoilCarbonTonnesCO2e",
            # server-computed outputs
            "AboveGroundBiomassTonnes", "BelowGroundBiomassTonnes", "TotalBiomassTonnes",
            "CarbonStockTonnesC", "CO2EquivalentTonnes", "TotalCarbonStockLossTonnesCO2e",
        )
        read_only_fields = (
            "AboveGroundBiomassTonnes", "BelowGroundBiomassTonnes", "TotalBiomassTonnes",
            "CarbonStockTonnesC", "CO2EquivalentTonnes", "TotalCarbonStockLossTonnesCO2e",
        )


class TreeRemovalAffectedSpeciesSerializer(TenantOwnedRelationshipsMixin, serializers.ModelSerializer):
    tenant_owned_relationships = {"SpeciesId": "EntityId_id"}

    class Meta:
        model = TreeRemovalAffectedSpecies
        fields = ("id", "SpeciesId", "Notes")


class RestorationsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restorations
        fields = ("RestorationId", "RestorationName", "RestorationReference",
                  "StartDate", "TotalTreesPlanted", "TotalAreaHectares", "Status")


class RestorationsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restorations
        fields = "__all__"
        # EstimatedCarbonSequestrationTonnes is server-computed (IPCC LULUCF); never trust client values.
        read_only_fields = ("RestorationId", "EntityId", "EstimatedCarbonSequestrationTonnes",
                            "CreatedAt", "UpdatedAt", "CreatedBy", "UpdatedBy")


class RestorationSpeciesSerializer(TenantOwnedRelationshipsMixin, serializers.ModelSerializer):
    tenant_owned_relationships = {"SpeciesId": "EntityId_id"}

    class Meta:
        model = RestorationSpecies
        fields = (
            "id", "SpeciesId", "Count",
            # client inputs
            "AreaHectares", "AnnualSequestrationRateTonnesCO2ePerHa", "SurvivalEstimate",
            "LeakageDiscountPercent", "PermanenceRisk", "AdditionalityAssessment",
            "SequestrationDataSource",
            # server-computed outputs
            "YearsEstablished", "CumulativeSequestrationTonnesCO2e",
        )
        read_only_fields = ("YearsEstablished", "CumulativeSequestrationTonnesCO2e")
