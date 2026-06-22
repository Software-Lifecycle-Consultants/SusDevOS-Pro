from rest_framework import serializers
from .models import LandParcels


class LandParcelsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandParcels
        fields = ("LandParcelId", "ParcelName", "ParcelReference", "AreaHectares",
                  "LandUseType", "Status")


class LandParcelsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandParcels
        fields = "__all__"
        read_only_fields = ("LandParcelId", "EntityId", "CreatedAt", "UpdatedAt", "CreatedBy", "UpdatedBy")
