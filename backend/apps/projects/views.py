from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.shared.views import TenantViewSetMixin
from .models import (
    DevelopmentProjectLandParcels, DevelopmentProjectPartners,
    DevelopmentProjects, ProjectPhases,
)
from .serializers import (
    DevelopmentProjectsDetailSerializer,
    DevelopmentProjectsListSerializer,
    ProjectPartnerSerializer,
    ProjectPhaseSerializer,
)


class DevelopmentProjectsViewSet(TenantViewSetMixin, ModelViewSet):
    queryset = DevelopmentProjects.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return DevelopmentProjectsListSerializer if self.action == "list" else DevelopmentProjectsDetailSerializer

    # ── Phases ─────────────────────────────────────────────────────────────────

    @action(detail=True, methods=["get", "post"], url_path="phases")
    def phases(self, request, pk=None):
        project = self.get_object()
        if request.method == "GET":
            qs = project.phases.filter(Status__lt=4)
            return Response(ProjectPhaseSerializer(qs, many=True).data)
        s = ProjectPhaseSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        phase = s.save(ProjectId=project, EntityId=project.EntityId, CreatedBy=request.user.UserId)
        return Response(ProjectPhaseSerializer(phase).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "patch", "delete"],
            url_path=r"phases/(?P<phase_id>\d+)")
    def phase_detail(self, request, pk=None, phase_id=None):
        project = self.get_object()
        phase = get_object_or_404(ProjectPhases, PhaseId=phase_id, ProjectId=project)
        if request.method == "GET":
            return Response(ProjectPhaseSerializer(phase).data)
        if request.method == "PATCH":
            s = ProjectPhaseSerializer(phase, data=request.data, partial=True)
            s.is_valid(raise_exception=True)
            s.save(UpdatedBy=request.user.UserId)
            return Response(ProjectPhaseSerializer(phase).data)
        phase.Status = 4
        phase.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── Partners ───────────────────────────────────────────────────────────────

    @action(detail=True, methods=["get", "post"], url_path="partners")
    def partners(self, request, pk=None):
        project = self.get_object()
        if request.method == "GET":
            qs = project.project_partners.all()
            return Response(ProjectPartnerSerializer(qs, many=True).data)
        s = ProjectPartnerSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        partner = s.save(ProjectId=project)
        return Response(ProjectPartnerSerializer(partner).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"partners/(?P<partner_id>\d+)")
    def remove_partner(self, request, pk=None, partner_id=None):
        project = self.get_object()
        get_object_or_404(DevelopmentProjectPartners, id=partner_id, ProjectId=project).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── Emissions summary ─────────────────────────────────────────────────────

    @action(detail=True, methods=["get"], url_path="emissions/summary")
    def emissions_summary(self, request, pk=None):
        from django.db.models import Sum
        from apps.emissions.models import EmissionsData
        project = self.get_object()
        qs = EmissionsData.objects.filter(ProjectId=project, Status__lt=4)
        def total(scope):
            result = qs.filter(Scope=scope).aggregate(t=Sum("EmissionsAmountTonnes"))["t"]
            return float(result or 0)
        return Response({
            "scope1_tonnes": total(1),
            "scope2_location_tonnes": float(
                qs.filter(Scope=2).aggregate(t=Sum("EmissionsAmountLocationBased"))["t"] or 0
            ) / 1000,
            "scope2_market_tonnes": float(
                qs.filter(Scope=2).aggregate(t=Sum("EmissionsAmountMarketBased"))["t"] or 0
            ) / 1000,
            "scope3_tonnes": total(3),
        })
