"""Reusable serializer guards for tenant-scoped domain relationships."""

from rest_framework import serializers


class TenantOwnedRelationshipsMixin:
    """Restrict related-object inputs to the request's active entity.

    Tenant-scoping a viewset's top-level queryset does not protect writes: DRF
    related fields otherwise resolve primary keys from their model's global
    queryset. Serializers opt in with ``tenant_owned_relationships`` mapping
    input field names to the related model's entity lookup.

    Input validation fails closed when the active entity context is missing.
    This is intentional: silently accepting an unscoped relationship is a
    tenant-isolation defect, not a recoverable serializer condition.
    """

    tenant_owned_relationships = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        entity_id = getattr(request, "entity_id", None)

        for field_name, entity_lookup in self.tenant_owned_relationships.items():
            field = self.fields.get(field_name)
            queryset = getattr(field, "queryset", None)
            if queryset is None:
                continue
            if entity_id is None:
                field.queryset = queryset.none()
            else:
                field.queryset = queryset.filter(**{entity_lookup: entity_id})

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get("request")
        entity_id = getattr(request, "entity_id", None)
        if entity_id is None:
            raise serializers.ValidationError(
                {"non_field_errors": ["An active entity is required for this operation."]}
            )

        errors = {}
        for field_name, entity_attr in self.tenant_owned_relationships.items():
            related = attrs.get(field_name)
            if related is None:
                continue
            if getattr(related, entity_attr, None) != entity_id:
                errors[field_name] = "The selected record does not belong to the active entity."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class RejectServerManagedInputMixin:
    """Reject, rather than silently discard, explicitly server-owned fields."""

    server_managed_input_fields = ()

    def to_internal_value(self, data):
        errors = {
            field: "This field is managed by the server and cannot be submitted."
            for field in self.server_managed_input_fields
            if field in data
        }
        if errors:
            raise serializers.ValidationError(errors)
        return super().to_internal_value(data)


class RejectUnknownFieldsMixin:
    """Return field-specific errors for payload keys outside the API contract."""

    def to_internal_value(self, data):
        errors = {
            field: "This field is not accepted by this endpoint."
            for field in data
            if field not in self.fields
        }
        if errors:
            raise serializers.ValidationError(errors)
        return super().to_internal_value(data)
