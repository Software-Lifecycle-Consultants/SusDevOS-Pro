from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.shared.views import TenantViewSetMixin
from .models import LandParcelEcosystems, LandParcels
from .serializers import LandParcelsDetailSerializer, LandParcelsListSerializer


class LandParcelsViewSet(TenantViewSetMixin, ModelViewSet):
    queryset = LandParcels.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return LandParcelsListSerializer if self.action == "list" else LandParcelsDetailSerializer

    @action(detail=True, methods=["get", "post"], url_path="ecosystems")
    def ecosystems(self, request, pk=None):
        parcel = self.get_object()
        if request.method == "GET":
            from apps.ecosystem.models import Ecosystem
            from apps.ecosystem.serializers import EcosystemListSerializer
            ids = LandParcelEcosystems.objects.filter(LandParcelId=parcel).values_list(
                "EcosystemId_id", flat=True)
            return Response(EcosystemListSerializer(
                Ecosystem.objects.filter(EcosystemId__in=ids), many=True).data)
        eco_id = request.data.get("EcosystemId")
        if not eco_id:
            return Response({"code": "required", "detail": "EcosystemId is required."},
                            status=status.HTTP_400_BAD_REQUEST)
        LandParcelEcosystems.objects.get_or_create(LandParcelId=parcel, EcosystemId_id=eco_id)
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"],
            url_path=r"ecosystems/(?P<ecosystem_id>\d+)")
    def unlink_ecosystem(self, request, pk=None, ecosystem_id=None):
        parcel = self.get_object()
        LandParcelEcosystems.objects.filter(
            LandParcelId=parcel, EcosystemId_id=ecosystem_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
