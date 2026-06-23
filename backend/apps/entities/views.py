from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.shared.models import Contacts, Documents, EntityApiKeys, Locations
from apps.shared.permissions import IsEntityAdmin, IsSuperAdmin
from .models import (
    Entities,
    EntityApiKeysIntermediary,
    EntityContacts,
    EntityDocuments,
    EntityLocations,
)
from .serializers import (
    ApiKeyCreateResponseSerializer,
    ApiKeyListSerializer,
    ContactSerializer,
    DocumentSerializer,
    EntitiesDetailSerializer,
    EntitiesListSerializer,
    EntityCreateSerializer,
    LocationSerializer,
)


class EntitiesViewSet(ModelViewSet):
    """
    CRUD for Entities.
    SA sees all; Admin sees own + related branches.
    Creation is SA-only and also creates the initial admin user.
    """
    permission_classes = [IsAuthenticated]
    queryset = Entities.objects.all()  # overridden by get_queryset; required by DRF router

    def initial(self, request, *args, **kwargs):
        """Re-resolve entity_id after DRF auth (middleware runs before auth)."""
        super().initial(request, *args, **kwargs)
        user = request.user
        header_id = request.META.get("HTTP_X_ENTITY_ID")
        if header_id:
            try:
                header_id = int(header_id)
            except (ValueError, TypeError):
                header_id = None
        if header_id and getattr(user, "IsSuperAdmin", False):  # SUPERADMIN_BYPASS
            request.entity_id = header_id
        elif header_id and getattr(user, "EntityId_id", None) == header_id:
            request.entity_id = header_id
        elif not getattr(request, "entity_id", None):
            request.entity_id = getattr(user, "EntityId_id", None)

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "IsSuperAdmin", False):  # SUPERADMIN_BYPASS
            return Entities.objects.filter(Status__lt=4)
        entity_id = self.request.entity_id
        if not entity_id:
            return Entities.objects.none()
        # Own entity + related branches
        related_ids = list(
            Entities.objects.filter(
                child_relations__ParentEntityId_id=entity_id
            ).values_list("EntityId", flat=True)
        )
        return Entities.objects.filter(
            EntityId__in=[entity_id] + related_ids, Status__lt=4
        )

    def get_serializer_class(self):
        if self.action == "create":
            return EntityCreateSerializer
        if self.action == "list":
            return EntitiesListSerializer
        return EntitiesDetailSerializer

    def create(self, request, *args, **kwargs):
        if not getattr(request.user, "IsSuperAdmin", False):
            return Response(
                {"code": "permission_denied", "detail": "Only SuperAdmin can create entities."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not getattr(request.user, "IsSuperAdmin", False):
            return Response(
                {"code": "permission_denied", "detail": "Only SuperAdmin can delete entities."},
                status=status.HTTP_403_FORBIDDEN,
            )
        instance = self.get_object()
        instance.Status = 4
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save()

    # ── Nested: Locations ─────────────────────────────────────────────────────

    @action(detail=True, methods=["get", "post"], url_path="locations")
    def locations(self, request, pk=None):
        entity = self.get_object()
        if request.method == "GET":
            locs = Locations.objects.filter(entity_locations__EntityId=entity)
            return Response(LocationSerializer(locs, many=True).data)

        serializer = LocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        location = Locations.objects.create(
            **serializer.validated_data,
            CreatedBy=request.user.UserId,
        )
        EntityLocations.objects.create(EntityId=entity, LocationId=location)
        return Response(LocationSerializer(location).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"locations/(?P<location_id>\d+)")
    def unlink_location(self, request, pk=None, location_id=None):
        entity = self.get_object()
        EntityLocations.objects.filter(
            EntityId=entity, LocationId_id=location_id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── Nested: Contacts ──────────────────────────────────────────────────────

    @action(detail=True, methods=["get", "post"], url_path="contacts")
    def contacts(self, request, pk=None):
        entity = self.get_object()
        if request.method == "GET":
            contacts = Contacts.objects.filter(entity_contacts__EntityId=entity, Status__lt=4)
            return Response(ContactSerializer(contacts, many=True).data)

        serializer = ContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = Contacts.objects.create(
            **serializer.validated_data,
            EntityId=entity.EntityId,
            CreatedBy=request.user.UserId,
        )
        from .models import EntityContacts
        EntityContacts.objects.create(EntityId=entity, ContactId=contact)
        return Response(ContactSerializer(contact).data, status=status.HTTP_201_CREATED)

    # ── Nested: Documents ─────────────────────────────────────────────────────

    @action(detail=True, methods=["get", "post"], url_path="documents")
    def documents(self, request, pk=None):
        entity = self.get_object()
        if request.method == "GET":
            docs = Documents.objects.filter(entity_documents__EntityId=entity, Status__lt=4)
            return Response(DocumentSerializer(docs, many=True).data)

        serializer = DocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc = Documents.objects.create(
            **serializer.validated_data,
            EntityId=entity.EntityId,
            CreatedBy=request.user.UserId,
        )
        EntityDocuments.objects.create(EntityId=entity, DocumentId=doc)
        return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)

    # ── Nested: API Keys ──────────────────────────────────────────────────────

    @action(detail=True, methods=["get", "post"], url_path="api-keys")
    def api_keys(self, request, pk=None):
        entity = self.get_object()
        if request.method == "GET":
            keys = EntityApiKeys.objects.filter(
                entity_links__EntityId=entity, Status__lt=4
            )
            return Response(ApiKeyListSerializer(keys, many=True).data)

        from apps.entities.services import generate_api_key
        result = generate_api_key(
            entity          = entity,
            created_by_user_id = request.user.UserId,
            name            = request.data.get("AuthorizedByFor", ""),
            expiry_date     = request.data.get("ExpiryDate"),
        )
        return Response(result, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"api-keys/(?P<key_id>\d+)")
    def revoke_api_key(self, request, pk=None, key_id=None):
        from apps.entities.services import revoke_api_key
        entity = self.get_object()
        key = get_object_or_404(EntityApiKeys, ApiKeyId=key_id, entity_links__EntityId=entity)
        revoke_api_key(key=key)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── Settings ──────────────────────────────────────────────────────────────

    @action(detail=True, methods=["get", "patch"], url_path="settings")
    def entity_settings(self, request, pk=None):
        entity = self.get_object()
        if request.method == "GET":
            return Response({
                "ShareEmissionsWithPartners": entity.ShareEmissionsWithPartners,
                "BaseCurrency":               entity.BaseCurrency,
                "FiscalYearEndMonth":         entity.FiscalYearEndMonth,
                "ConsolidationApproach":      entity.ConsolidationApproach,
            })
        allowed = {"ShareEmissionsWithPartners", "BaseCurrency", "FiscalYearEndMonth", "ConsolidationApproach"}
        for field, value in request.data.items():
            if field in allowed:
                setattr(entity, field, value)
        entity.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
