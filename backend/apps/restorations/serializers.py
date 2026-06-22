from rest_framework import serializers
from .models import (
    TreeRemovals, TreeRemovalRemovedSpecies, TreeRemovalAffectedSpecies,
    Restorations, RestorationSpecies,
)


class TreeRemovalsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreeRemovals
        fields = ("TreeRemovalId", "ProjectId", "RemovalDate",
                  "TotalTreesRemoved", "TotalBiomassCarbon", "Status")


class TreeRemovalsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreeRemovals
        fields = "__all__"
        read_only_fields = ("TreeRemovalId", "EntityId", "CreatedAt", "UpdatedAt", "CreatedBy", "UpdatedBy")


class TreeRemovalSpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreeRemovalRemovedSpecies
        fields = ("id", "SpeciesId", "Count")


class TreeRemovalAffectedSpeciesSerializer(serializers.ModelSerializer):
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
        read_only_fields = ("RestorationId", "EntityId", "CreatedAt", "UpdatedAt", "CreatedBy", "UpdatedBy")


class RestorationSpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestorationSpecies
        fields = ("id", "SpeciesId", "Count")
