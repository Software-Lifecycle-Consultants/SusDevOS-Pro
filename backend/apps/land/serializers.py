from decimal import Decimal

from rest_framework import serializers

from .geo import area_hectares
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

    def validate_BoundaryGeoJSON(self, value):  # noqa: N802 — DRF resolves validators by exact field name
        """Reject anything that is not a GeoJSON object.

        The column is a plain JSONField, so without this any JSON at all would be
        stored and the map would silently render nothing.
        """
        if value in (None, "", {}):
            return None
        if not isinstance(value, dict) or not value.get("type"):
            raise serializers.ValidationError(
                "Expected a GeoJSON object with a \"type\" - for example "
                '{"type": "Polygon", "coordinates": [...]}.'
            )
        return value

    def validate(self, attrs):
        """Derive AreaHectares from the boundary so the number matches the shape.

        Applied whenever a boundary is written without a non-empty area in the same
        payload. Sending a real AreaHectares alongside the boundary overrides the
        calculation, which a user needs when the legal title area differs from the
        mapped polygon.

        Presence alone is not treated as an override: the create form always sends
        the key, as null when the field is blank, so keying off presence would mean
        the derivation never fired.

        Point pins and lines enclose no area, so area_hectares() returns None and
        any existing value is left alone rather than being zeroed.
        """
        attrs = super().validate(attrs)

        if "BoundaryGeoJSON" not in attrs:
            return attrs

        initial = getattr(self, "initial_data", None)
        supplied = initial.get("AreaHectares") if isinstance(initial, dict) else None
        if supplied not in (None, ""):
            return attrs

        derived = area_hectares(attrs.get("BoundaryGeoJSON"))
        if derived is not None:
            attrs["AreaHectares"] = Decimal(f"{derived:.4f}")
        return attrs
