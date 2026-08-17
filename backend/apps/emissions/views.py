"""
Emissions API views.

Critical rules enforced here:
  1. EmissionsAmount is NEVER accepted from client — always server-computed.
  2. VerificationStatus >= 3 → PATCH/DELETE blocked (HTTP 403).
  3. Biogenic CO2 excluded from GWP total (enforced in model.save()).
  4. Scope 2 always computes both location-based and market-based.
"""
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.billing.mixins import FeatureGateMixin
from apps.shared.views import TenantViewSetMixin

from .models import (
    EmissionFactors,
    EmissionFactorSets,
    EmissionsData,
    EmissionsDetails,
    EmissionsOffsets,
    GHGInventories,
    GwpDatasets,
    Targets,
)
from .serializers import (
    EmissionFactorSetsSerializer,
    EmissionFactorsSerializer,
    EmissionsDataListSerializer,
    EmissionsDataSerializer,
    EmissionsDetailsSerializer,
    EmissionsOffsetsSerializer,
    GHGInventoriesSerializer,
    GwpDatasetsSerializer,
    TargetMilestonesSerializer,
    TargetsSerializer,
)

VERIFIED = 3  # VerificationStatus >= VERIFIED → immutable


class EmissionsDataViewSet(TenantViewSetMixin, ModelViewSet):
    queryset = EmissionsData.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return EmissionsDataListSerializer if self.action == "list" else EmissionsDataSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if p.get("projectId"):
            qs = qs.filter(ProjectId=p["projectId"])
        if p.get("scope"):
            qs = qs.filter(Scope=p["scope"])
        if p.get("phaseId"):
            qs = qs.filter(PhaseId=p["phaseId"])
        if p.get("verificationStatus"):
            qs = qs.filter(VerificationStatus=p["verificationStatus"])
        if p.get("reportingYear"):
            qs = qs.filter(ReportingYear=p["reportingYear"])
        return qs

    @staticmethod
    def _inventory_locked_response(inventory):
        """Return a 403 if the row's parent GHG inventory is verified.

        A verified inventory (VerificationStatus >= 3) is immutable (CLAUDE.md
        rule #3) and its totals are frozen — the nightly recompute explicitly
        skips verified inventories (tasks/emissions.py). Allowing a client to
        edit, delete, or add the underlying EmissionsData rows would silently
        diverge the audit-locked totals from the data they represent, so the
        row-level guard must also honour the parent inventory's lock."""
        if inventory is not None and inventory.VerificationStatus >= VERIFIED:
            return Response(
                {"code": "verified_immutable",
                 "detail": "This record belongs to a verified GHG inventory and cannot be changed. Unlock the inventory first (SuperAdmin only)."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    def _require_scope3_feature(self, validated_data):
        """Scope 3 emissions accounting is a Starter+ feature (``scope_3``).

        The record is calculated server-side regardless of the frontend, so the
        gate must live on the write path, not just the UI (CLAUDE.md rule #6:
        feature gates are server-enforced, never frontend-only). Scope 1 and 2
        stay available on all plans, so this gates only the Scope 3 case rather
        than the whole viewset."""
        if validated_data.get("Scope") != 3:
            return
        if getattr(self.request.user, "IsSuperAdmin", False):  # SUPERADMIN_BYPASS
            return
        from apps.billing.mixins import FeatureGatedException
        from apps.billing.services import get_upgrade_message, is_feature_enabled
        entity_id = getattr(self.request, "entity_id", None)
        if not entity_id or not is_feature_enabled(entity_id=entity_id, feature_key="scope_3"):
            raise FeatureGatedException(
                feature_key="scope_3",
                message=get_upgrade_message(feature_key="scope_3"),
            )

    def perform_create(self, serializer):
        # GwpDatasetId defaults to system default if not provided
        if not serializer.validated_data.get("GwpDatasetId"):
            default = GwpDatasets.objects.filter(IsDefault=True).first()
            serializer.validated_data["GwpDatasetId"] = default
        serializer.save(
            EntityId_id=self.request.entity_id,
            CreatedBy=self.request.user.UserId,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._require_scope3_feature(serializer.validated_data)
        locked = self._inventory_locked_response(serializer.validated_data.get("InventoryId"))
        if locked:
            return locked
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        if instance.VerificationStatus >= VERIFIED:
            return Response(
                {"code": "verified_immutable",
                 "detail": "Verified records cannot be edited. Use /unlock/ first (SuperAdmin only)."},
                status=status.HTTP_403_FORBIDDEN,
            )
        locked = self._inventory_locked_response(instance.InventoryId)
        if locked:
            return locked
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self._require_scope3_feature(serializer.validated_data)
        # Block re-pointing this row INTO a (different) verified inventory. The
        # guards above only see the row's *current* InventoryId; InventoryId is
        # client-writable, so without this a PATCH could attach an unverified
        # row to a frozen inventory — a bypass of rule #3. create() already
        # validates the *target* inventory, so this makes update() consistent.
        target_inv = serializer.validated_data.get("InventoryId")
        if target_inv is not None and target_inv != instance.InventoryId:
            locked = self._inventory_locked_response(target_inv)
            if locked:
                return locked
        self.perform_update(serializer)
        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.VerificationStatus >= VERIFIED:
            return Response(
                {"code": "verified_immutable",
                 "detail": "Verified records cannot be deleted."},
                status=status.HTTP_403_FORBIDDEN,
            )
        locked = self._inventory_locked_response(instance.InventoryId)
        if locked:
            return locked
        return super().destroy(request, *args, **kwargs)

    # ── Verify ─────────────────────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        instance = self.get_object()
        if instance.VerificationStatus >= VERIFIED:
            return Response({"code": "already_verified", "detail": "Already verified."},
                            status=status.HTTP_400_BAD_REQUEST)
        from apps.emissions.services import verify_record
        verify_record(instance, verified_by=request.user, notes=request.data.get("notes", ""))
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── Unlock (SuperAdmin only) ───────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="unlock")
    def unlock(self, request, pk=None):
        if not getattr(request.user, "IsSuperAdmin", False):  # SUPERADMIN_BYPASS
            return Response({"code": "permission_denied",
                             "detail": "Only SuperAdmin can unlock verified records."},
                            status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        reason = request.data.get("reason", "")
        if not reason:
            return Response({"code": "reason_required",
                             "detail": "A reason is required to unlock a verified record."},
                            status=status.HTTP_400_BAD_REQUEST)
        from apps.emissions.services import unlock_record
        unlock_record(instance, reason=reason, unlocked_by=request.user, entity_id=request.entity_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @classmethod
    def _verified_lock_response(cls, record):
        """Return a 403 Response if the record's line items are locked, else None.

        Detail/offset line items feed the recomputed emissions total, so allowing
        them to change on a locked record would mutate the audit-locked figure
        without going through the SuperAdmin unlock path (CLAUDE.md rule #3).

        Two independent locks apply, mirroring the record-level create/update/
        destroy guards:
          * the record's own VerificationStatus (individually verified row), and
          * the parent GHG inventory's VerificationStatus. A verified inventory
            freezes its member rows even when a given row was never individually
            verified — otherwise nested line-item writes are a bypass of the
            inventory lock the record-level paths already enforce."""
        if record.VerificationStatus >= VERIFIED:
            return Response(
                {"code": "verified_immutable",
                 "detail": "Line items of a verified record cannot be changed. Use /unlock/ first (SuperAdmin only)."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return cls._inventory_locked_response(record.InventoryId)

    # ── Details (line items) ───────────────────────────────────────────────────

    @action(detail=True, methods=["get", "post"], url_path="details")
    def details(self, request, pk=None):
        record = self.get_object()
        if request.method == "GET":
            return Response(EmissionsDetailsSerializer(
                record.details.filter(Status__lt=4), many=True).data)
        locked = self._verified_lock_response(record)
        if locked:
            return locked
        s = EmissionsDetailsSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        detail = s.save(EmissionsId=record, EntityId_id=request.entity_id,
                        CreatedBy=request.user.UserId)
        return Response(EmissionsDetailsSerializer(detail).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch", "delete"],
            url_path=r"details/(?P<detail_id>\d+)")
    def detail_item(self, request, pk=None, detail_id=None):
        record = self.get_object()
        locked = self._verified_lock_response(record)
        if locked:
            return locked
        item = get_object_or_404(EmissionsDetails, DetailId=detail_id, EmissionsId=record)
        if request.method == "PATCH":
            s = EmissionsDetailsSerializer(item, data=request.data, partial=True)
            s.is_valid(raise_exception=True)
            s.save()
            return Response(EmissionsDetailsSerializer(item).data)
        item.Status = 4
        item.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── Offsets ────────────────────────────────────────────────────────────────

    @action(detail=True, methods=["get", "post"], url_path="offsets")
    def offsets(self, request, pk=None):
        record = self.get_object()
        if request.method == "GET":
            return Response(EmissionsOffsetsSerializer(
                record.offsets.filter(Status__lt=4), many=True).data)
        locked = self._verified_lock_response(record)
        if locked:
            return locked
        s = EmissionsOffsetsSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        offset = s.save(EmissionsId=record, EntityId_id=request.entity_id,
                        CreatedBy=request.user.UserId)
        return Response(EmissionsOffsetsSerializer(offset).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch", "delete"],
            url_path=r"offsets/(?P<offset_id>\d+)")
    def offset_item(self, request, pk=None, offset_id=None):
        record = self.get_object()
        locked = self._verified_lock_response(record)
        if locked:
            return locked
        item = get_object_or_404(EmissionsOffsets, OffsetId=offset_id, EmissionsId=record)
        if request.method == "PATCH":
            s = EmissionsOffsetsSerializer(item, data=request.data, partial=True)
            s.is_valid(raise_exception=True)
            s.save()
            return Response(EmissionsOffsetsSerializer(item).data)
        item.Status = 4
        item.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmissionsOffsetsViewSet(FeatureGateMixin, TenantViewSetMixin, ModelViewSet):
    """
    Standalone offset management — GET /api/emissions-offsets/
    Lists all offsets for the entity regardless of which emissions record they
    belong to, so the sustainability manager has a single place to review them.
    The nested actions on EmissionsDataViewSet remain for record-level access.
    """
    required_feature = "carbon_offsets"
    queryset         = EmissionsOffsets.objects.all()
    serializer_class = EmissionsOffsetsSerializer
    permission_classes = [IsAuthenticated]
    lookup_field     = "OffsetId"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def _parent_verified_response(self, instance):
        """Return a 403 if the offset's parent emissions record is locked.

        Offsets feed the recomputed net emissions total, so editing or deleting
        one attached to a locked record would mutate the audit-locked figure
        without going through /unlock/ — the same guard the nested offset actions
        on EmissionsDataViewSet already enforce (CLAUDE.md rule #3). This
        standalone viewset must not be a bypass.

        The record is locked when either its own VerificationStatus is verified
        or its parent GHG inventory is verified (a verified inventory freezes its
        member rows even when the row itself was never individually verified)."""
        record = instance.EmissionsId
        if record is None:
            return None
        if record.VerificationStatus >= VERIFIED:
            return Response(
                {"code": "verified_immutable",
                 "detail": "Offsets on a verified emissions record cannot be changed. Use /unlock/ first (SuperAdmin only)."},
                status=status.HTTP_403_FORBIDDEN,
            )
        inventory = record.InventoryId
        if inventory is not None and inventory.VerificationStatus >= VERIFIED:
            return Response(
                {"code": "verified_immutable",
                 "detail": "Offsets on a record in a verified GHG inventory cannot be changed. Unlock the inventory first (SuperAdmin only)."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    def update(self, request, *args, **kwargs):
        err = self._parent_verified_response(self.get_object())
        if err:
            return err
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        err = self._parent_verified_response(self.get_object())
        if err:
            return err
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(
            EntityId_id = self.request.entity_id,
            CreatedBy   = self.request.user.UserId,
        )

    def perform_destroy(self, instance):
        instance.Status = 4
        instance.save()


class GwpDatasetsViewSet(ReadOnlyModelViewSet):
    """GWP datasets are read-only — seeded, not user-created."""
    queryset = GwpDatasets.objects.filter(Status=1)
    serializer_class = GwpDatasetsSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "GwpDatasetId"


class GHGInventoriesViewSet(FeatureGateMixin, TenantViewSetMixin, ModelViewSet):
    required_feature = "ghg_inventory_formal"
    queryset = GHGInventories.objects.all()
    serializer_class = GHGInventoriesSerializer
    permission_classes = [IsAuthenticated]

    def _check_not_verified(self, instance):
        if instance.VerificationStatus >= VERIFIED:
            return Response({"code": "verified_immutable",
                             "detail": "Verified inventories cannot be edited or deleted."},
                            status=status.HTTP_403_FORBIDDEN)
        return None

    def update(self, request, *args, **kwargs):
        err = self._check_not_verified(self.get_object())
        if err:
            return err
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        err = self._check_not_verified(self.get_object())
        if err:
            return err
        return super().destroy(request, *args, **kwargs)

    def perform_update(self, serializer):
        """Record who verified the inventory and when, on the transition to
        Verified (VerificationStatus >= 3).  Without this an inventory could
        become verified with no provenance — unacceptable for MRV/audit."""
        extra = {}
        new_status = serializer.validated_data.get("VerificationStatus")
        if (
            new_status is not None
            and new_status >= VERIFIED
            and serializer.instance.VerificationStatus < VERIFIED
        ):
            extra = {"VerifiedBy": self.request.user, "VerifiedAt": timezone.now()}
        instance = serializer.save(UpdatedBy=self.request.user.UserId, **extra)
        self._audit("Update", instance)
        return instance

    @action(detail=True, methods=["post"], url_path="unlock")
    def unlock(self, request, pk=None):
        """Reset a verified inventory to Unverified. SuperAdmin only; audited."""
        if not getattr(request.user, "IsSuperAdmin", False):  # SUPERADMIN_BYPASS
            return Response({"code": "permission_denied",
                             "detail": "Only SuperAdmin can unlock verified inventories."},
                            status=status.HTTP_403_FORBIDDEN)
        inventory = self.get_object()
        reason = request.data.get("reason", "")
        if not reason:
            return Response({"code": "reason_required",
                             "detail": "A reason is required to unlock a verified inventory."},
                            status=status.HTTP_400_BAD_REQUEST)
        inventory.VerificationStatus = 1
        inventory.VerifiedBy = None
        inventory.VerifiedAt = None
        inventory.save(update_fields=["VerificationStatus", "VerifiedBy", "VerifiedAt"])

        from apps.shared.audit import audit_log
        audit_log(
            action="Unlock_Verified", table_name="ghg_inventories",
            record_id=inventory.InventoryId,
            description=f"Unlocked verified inventory. Reason: {reason}",
            request=request, retention_tier=3,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TargetsViewSet(TenantViewSetMixin, ModelViewSet):
    queryset = Targets.objects.all()
    serializer_class = TargetsSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["get", "post"], url_path="milestones")
    def milestones(self, request, pk=None):
        target = self.get_object()
        if request.method == "GET":
            return Response(TargetMilestonesSerializer(
                target.milestones.filter(Status__lt=4), many=True).data)
        s = TargetMilestonesSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        m = s.save(TargetId=target, EntityId_id=request.entity_id,
                   CreatedBy=request.user.UserId)
        return Response(TargetMilestonesSerializer(m).data, status=status.HTTP_201_CREATED)


# ── Emission factor library (global reference data — no tenant scope) ──────────

class EmissionFactorSetsViewSet(ReadOnlyModelViewSet):
    """
    Read-only list of emission factor sets (DEFRA, EPA eGRID, Climatiq, etc.).
    GET /api/emission-factor-sets/
    """
    queryset         = EmissionFactorSets.objects.filter(IsActive=True, Status=1)
    serializer_class = EmissionFactorSetsSerializer
    permission_classes = [IsAuthenticated]
    lookup_field     = "SetId"
    filter_backends  = [OrderingFilter]
    ordering_fields  = ["SetName", "Publisher", "ApplicableYear"]
    ordering         = ["-ApplicableYear", "SetName"]


class EmissionFactorsViewSet(ReadOnlyModelViewSet):
    """
    Browsable emission factor library.

    GET /api/emission-factors/
    Supports:
      ?search=       full-text search on ActivityName and ActivityCategory
      ?scope=        filter by Scope (1, 2, 3)
      ?scope3=       filter by Scope3Category (1–15)
      ?set_id=       filter by EmissionFactorSets.SetId
      ?gas=          filter by Gas (CO2, CH4, N2O …)
      ?country=      filter by CountryCode (ISO2)
      ?year=         filter by ApplicableYear
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = EmissionFactorsSerializer
    lookup_field       = "FactorId"
    filter_backends    = [SearchFilter, OrderingFilter]
    search_fields      = ["ActivityName", "ActivityCategory"]
    ordering_fields    = ["ActivityName", "FactorValue", "ApplicableYear"]
    ordering           = ["ActivityName"]

    def get_queryset(self):
        qs = EmissionFactors.objects.filter(
            Status=1,
            SetId__IsActive=True,
            SetId__Status=1,
        ).select_related("SetId", "InputUnitId")

        p = self.request.query_params
        if p.get("scope"):
            qs = qs.filter(Scope=p["scope"])
        if p.get("scope3"):
            qs = qs.filter(Scope3Category=p["scope3"])
        if p.get("set_id"):
            qs = qs.filter(SetId=p["set_id"])
        if p.get("gas"):
            qs = qs.filter(Gas__iexact=p["gas"])
        if p.get("country"):
            qs = qs.filter(CountryCode__iexact=p["country"])
        if p.get("year"):
            qs = qs.filter(ApplicableYear=p["year"])
        return qs
