from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.viewsets import ModelViewSet

from apps.billing.mixins import FeatureGateMixin
from apps.shared.views import TenantViewSetMixin

from .models import LandParcelEcosystems, LandParcels
from .serializers import LandParcelsDetailSerializer, LandParcelsListSerializer


class LandParcelsViewSet(FeatureGateMixin, TenantViewSetMixin, ModelViewSet):
    # Declared but inert: settings.FEATURE_GATES_ENABLED is False, so land parcels
    # are available on every plan. Kept so gating is a settings flip, not a rewrite.
    required_feature = "land_parcel_gis"
    queryset = LandParcels.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return LandParcelsListSerializer if self.action == "list" else LandParcelsDetailSerializer

    @action(
        detail=False,
        methods=["get"],
        url_path="geocode",
        throttle_classes=[ScopedRateThrottle],
    )
    def geocode(self, request):
        """Place-name search for the boundary map. GET ?q=<place>[&limit=n].

        Reference lookup, not tenant data, so it is not entity-scoped — same shape
        as the GBIF species search on SpeciesViewSet. Proxied rather than called
        from the browser so the provider sees our User-Agent and cache, not the
        tenant's IP.
        """
        from .integrations import search_places

        try:
            limit = int(request.query_params.get("limit", 5))
        except (TypeError, ValueError):
            limit = 5
        return Response(search_places(request.query_params.get("q", ""), limit=limit))

    geocode.throttle_scope = "geocode"

    @action(detail=True, methods=["get", "post"], url_path="ecosystems")
    def ecosystems(self, request, pk=None):
        parcel = self.get_object()
        # The parcel is already tenant-scoped by TenantViewSetMixin.get_queryset;
        # scope every ecosystem operation to the same entity so a client cannot
        # read or link another tenant's ecosystem via a body-supplied id
        # (CLAUDE.md critical rule #2).
        from apps.ecosystem.models import Ecosystem
        parcel_entity_id = parcel.EntityId_id
        if request.method == "GET":
            from apps.ecosystem.serializers import EcosystemListSerializer
            ids = LandParcelEcosystems.objects.filter(LandParcelId=parcel).values_list(
                "EcosystemId_id", flat=True)
            return Response(EcosystemListSerializer(
                Ecosystem.objects.filter(
                    EcosystemId__in=ids, EntityId=parcel_entity_id, Status__lt=4
                ), many=True).data)
        eco_id = request.data.get("EcosystemId")
        if not eco_id:
            return Response({"code": "required", "detail": "EcosystemId is required."},
                            status=status.HTTP_400_BAD_REQUEST)
        if not Ecosystem.objects.filter(
            EcosystemId=eco_id, EntityId=parcel_entity_id, Status__lt=4
        ).exists():
            return Response(
                {"code": "not_found",
                 "detail": "Ecosystem not found for this entity."},
                status=status.HTTP_404_NOT_FOUND,
            )
        LandParcelEcosystems.objects.get_or_create(LandParcelId=parcel, EcosystemId_id=eco_id)
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"],
            url_path=r"ecosystems/(?P<ecosystem_id>\d+)")
    def unlink_ecosystem(self, request, pk=None, ecosystem_id=None):
        parcel = self.get_object()
        LandParcelEcosystems.objects.filter(
            LandParcelId=parcel, EcosystemId_id=ecosystem_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
