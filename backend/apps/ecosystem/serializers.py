from rest_framework import serializers

from .models import Ecosystem, Species


class EcosystemListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ecosystem
        fields = ("EcosystemId", "EcosystemName", "EcosystemType", "AreaHectares", "Status")


class EcosystemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ecosystem
        fields = "__all__"
        read_only_fields = ("EcosystemId", "EntityId", "CreatedAt", "UpdatedAt", "CreatedBy", "UpdatedBy")


class SpeciesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Species
        fields = ("SpeciesId", "CommonName", "ScientificName", "IUCNStatus", "Family", "Status")


class SpeciesDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Species
        fields = "__all__"
        read_only_fields = ("SpeciesId", "EntityId", "IUCNSyncedAt", "CreatedAt", "UpdatedAt", "CreatedBy", "UpdatedBy")
