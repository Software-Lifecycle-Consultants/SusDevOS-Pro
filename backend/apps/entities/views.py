from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.shared.models import Contacts, Documents, Locations

from .models import (
    Entities,
    EntityContacts,
    EntityDocuments,
    EntityLocations,
    EntityMembers,
)
from .serializers import (
    ContactSerializer,
    DocumentSerializer,
    EntitiesDetailSerializer,
    EntitiesListSerializer,
    EntityCreateSerializer,
    LocationSerializer,
)
from .services import accessible_entity_ids, user_can_access_entity


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
        elif header_id and user_can_access_entity(user, header_id):
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

    def _is_entity_admin(self, request) -> bool:
        """True if the caller is SuperAdmin or holds the entity 'admin' role.

        Mirrors apps.shared.permissions.IsEntityAdmin; used inline so privileged
        nested actions return the viewset's standard permission_denied envelope.
        """
        user = request.user
        if getattr(user, "IsSuperAdmin", False):  # SUPERADMIN_BYPASS
            return True
        return user.user_roles.filter(RoleId__RoleKey="admin", Status=1).exists()

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
        entity = serializer.save()
        from apps.notifications.services import notify
        notify(
            user_id=self.request.user.UserId,
            entity_id=entity.EntityId,
            type="entity_created",
            title="New entity created",
            body=f"Entity '{getattr(entity, 'EntityName', entity.EntityId)}' was created.",
            related_module="entities",
            related_record_id=entity.EntityId,
        )

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
        # Settings govern data-sharing (ShareEmissionsWithPartners) and the base
        # currency that drives FX conversions — mutation is entity-admin only.
        if not self._is_entity_admin(request):
            return Response(
                {"code": "permission_denied", "detail": "Only entity admins can change entity settings."},
                status=status.HTTP_403_FORBIDDEN,
            )
        allowed = {"ShareEmissionsWithPartners", "BaseCurrency", "FiscalYearEndMonth", "ConsolidationApproach"}
        for field, value in request.data.items():
            if field in allowed:
                setattr(entity, field, value)
        entity.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── Consolidation roll-up (G20) ─────────────────────────────────────────────

    @action(detail=True, methods=["get"], url_path="consolidated-emissions")
    def consolidated_emissions(self, request, pk=None):
        """
        Consolidated Scope 1/2/3 for the entity + its subsidiaries per the
        GHG Protocol consolidation approach (ghg_calculation_spec §9).
        Query params: ?year=YYYY (default current year), ?approach=1|2|3 (override).
        """
        from datetime import date

        from apps.entities.services import compute_consolidated_emissions

        entity = self.get_object()  # scoped by get_queryset (own + branches / SA)
        try:
            year = int(request.query_params.get("year", date.today().year))
        except (ValueError, TypeError):
            return Response({"code": "invalid_year", "detail": "year must be an integer."},
                            status=status.HTTP_400_BAD_REQUEST)
        approach = request.query_params.get("approach")
        approach = int(approach) if approach and approach.isdigit() else None

        data = compute_consolidated_emissions(entity=entity, reporting_year=year, approach=approach)
        return Response(data)

    # ── Multi-entity membership (G21) ───────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="accessible")
    def accessible(self, request):
        """Entities the current user can switch into (primary + memberships).
        Drives the frontend entity switcher. SuperAdmin sees all active entities."""
        if getattr(request.user, "IsSuperAdmin", False):
            qs = Entities.objects.filter(Status__lt=4)
        else:
            qs = Entities.objects.filter(
                EntityId__in=accessible_entity_ids(request.user), Status__lt=4)
        primary = getattr(request.user, "EntityId_id", None)
        return Response([
            {"EntityId": e.EntityId, "EntityName": e.EntityName, "IsPrimary": e.EntityId == primary}
            for e in qs.order_by("EntityName")
        ])

    @action(detail=True, methods=["get", "post"], url_path="members")
    def members(self, request, pk=None):
        """GET: list members of this entity. POST (SuperAdmin): grant a user access."""
        entity = self.get_object()
        if request.method == "GET":
            links = EntityMembers.objects.filter(EntityId=entity).select_related("UserId")
            return Response([
                {"UserId": m.UserId.UserId, "username": m.UserId.username, "email": m.UserId.email}
                for m in links
            ])

        if not getattr(request.user, "IsSuperAdmin", False):
            return Response({"code": "permission_denied", "detail": "Only SuperAdmin can grant entity access."},
                            status=status.HTTP_403_FORBIDDEN)

        from apps.users.models import Users
        ident = request.data.get("UserId") or request.data.get("email")
        if not ident:
            return Response({"code": "missing_user", "detail": "Provide UserId or email."},
                            status=status.HTTP_400_BAD_REQUEST)
        lookup = {"UserId": ident} if str(ident).isdigit() else {"email": ident}
        user = get_object_or_404(Users, **lookup)

        EntityMembers.objects.get_or_create(
            UserId=user, EntityId=entity,
            defaults={"CreatedBy": request.user.UserId},
        )
        return Response({"UserId": user.UserId, "username": user.username, "email": user.email},
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"members/(?P<user_id>\d+)")
    def remove_member(self, request, pk=None, user_id=None):
        if not getattr(request.user, "IsSuperAdmin", False):
            return Response({"code": "permission_denied", "detail": "Only SuperAdmin can revoke entity access."},
                            status=status.HTTP_403_FORBIDDEN)
        entity = self.get_object()
        EntityMembers.objects.filter(EntityId=entity, UserId_id=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
