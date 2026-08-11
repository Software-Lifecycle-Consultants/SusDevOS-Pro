"""
Emissions API views.

Critical rules enforced here:
  1. EmissionsAmount is NEVER accepted from client — always server-computed.
  2. VerificationStatus >= 3 → PATCH/DELETE blocked (HTTP 403).
  3. Biogenic CO2 excluded from GWP total (enforced in model.save()).
  4. Scope 2 always computes both location-based and market-based.
"""
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from rest_framework.filters import OrderingFilter, SearchFilter

from apps.billing.mixins import FeatureGateMixin
from apps.shared.views import TenantViewSetMixin
from .models import (
    EmissionFactorSets, EmissionFactors,
    EmissionsData, EmissionsDetails, EmissionsOffsets,
    GHGInventories, GwpDatasets, Targets, TargetMilestones,
)
from .serializers import (
    EmissionFactorSetsSerializer, EmissionFactorsSerializer,
    EmissionsDataListSerializer, EmissionsDataSerializer,
    EmissionsDetailsSerializer, EmissionsOffsetsSerializer,
    GHGInventoriesSerializer, GwpDatasetsSerializer,
    TargetMilestonesSerializer, TargetsSerializer,
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

    def perform_create(self, serializer):
        # GwpDatasetId defaults to system default if not provided
        if not serializer.validated_data.get("GwpDatasetId"):
            default = GwpDatasets.objects.filter(IsDefault=True).first()
            serializer.validated_data["GwpDatasetId"] = default
        serializer.save(
            EntityId_id=self.request.entity_id,
            CreatedBy=self.request.user.UserId,
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.VerificationStatus >= VERIFIED:
            return Response(
                {"code": "verified_immutable",
                 "detail": "Verified records cannot be edited. Use /unlock/ first (SuperAdmin only)."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.VerificationStatus >= VERIFIED:
            return Response(
                {"code": "verified_immutable",
                 "detail": "Verified records cannot be deleted."},
                status=status.HTTP_403_FORBIDDEN,
            )
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

    @staticmethod
    def _verified_lock_response(record):
        """Return a 403 Response if the parent record is verified, else None.

        Detail/offset line items feed the recomputed emissions total, so allowing
        them to change on a verified record would mutate the audit-locked figure
        without going through the SuperAdmin unlock path (CLAUDE.md rule #3)."""
        if record.VerificationStatus >= VERIFIED:
            return Response(
                {"code": "verified_immutable",
                 "detail": "Line items of a verified record cannot be changed. Use /unlock/ first (SuperAdmin only)."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

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
