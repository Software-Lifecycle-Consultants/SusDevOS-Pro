from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.billing.mixins import FeatureGateMixin
from apps.shared.views import TenantViewSetMixin

from .models import Ecosystem, Species
from .serializers import (
    EcosystemDetailSerializer,
    EcosystemListSerializer,
    SpeciesDetailSerializer,
    SpeciesListSerializer,
)


class EcosystemViewSet(FeatureGateMixin, TenantViewSetMixin, ModelViewSet):
    """Ecosystem.EntityId is a real FK to entities.Entities; tenant scoping,
    audit logging and soft-delete are provided by TenantViewSetMixin."""
    # Ecosystem tracking is a Starter+ feature (CLAUDE.md rule #6: feature
    # gates are server-enforced, never frontend-only).
    required_feature = "ecosystem_basic"
    permission_classes = [IsAuthenticated]
    queryset = Ecosystem.objects.all()

    def get_serializer_class(self):
        return EcosystemListSerializer if self.action == "list" else EcosystemDetailSerializer


class SpeciesViewSet(FeatureGateMixin, TenantViewSetMixin, ModelViewSet):
    """Species.EntityId is a real FK to entities.Entities; tenant scoping,
    audit logging and soft-delete are provided by TenantViewSetMixin."""
    # Species/biodiversity tracking is part of ecosystem tracking — Starter+
    # (CLAUDE.md rule #6: feature gates are server-enforced, not frontend-only).
    required_feature = "ecosystem_basic"
    permission_classes = [IsAuthenticated]
    queryset = Species.objects.all()

    def get_serializer_class(self):
        return SpeciesListSerializer if self.action == "list" else SpeciesDetailSerializer

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        """GBIF taxonomy lookup. GET ?q=<common or scientific name> → top matches."""
        from .integrations import search_species
        return Response(search_species(request.query_params.get("q", "")))

    def perform_create(self, serializer):
        instance = super().perform_create(serializer)
        # Best-effort GBIF/IUCN enrichment (never blocks create on external failure).
        from .integrations import enrich_species
        try:
            enrich_species(instance)
        except Exception:  # defensive — integrations already swallow errors
            pass
        return instance
