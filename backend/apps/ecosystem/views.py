from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.billing.mixins import FeatureGateMixin
from apps.shared.views import EntityScopeInitialMixin

from .models import Ecosystem, Species
from .serializers import (
    EcosystemDetailSerializer,
    EcosystemListSerializer,
    SpeciesDetailSerializer,
    SpeciesListSerializer,
)


class EcosystemViewSet(FeatureGateMixin, EntityScopeInitialMixin, ModelViewSet):
    """Ecosystem uses IntegerField for EntityId — uses a custom queryset filter.

    Ecosystem tracking is a Starter+ feature (spec/pricing.md), so it is gated
    server-side (CLAUDE.md rule #6). FeatureGateMixin is first in the MRO so its
    initial() runs after EntityScopeInitialMixin has resolved request.entity_id.
    """
    required_feature = "ecosystem_basic"
    permission_classes = [IsAuthenticated]
    queryset = Ecosystem.objects.all()

    def get_serializer_class(self):
        return EcosystemListSerializer if self.action == "list" else EcosystemDetailSerializer

    def get_queryset(self):
        qs = Ecosystem.objects.filter(Status__lt=4)
        user = self.request.user
        if getattr(user, "IsSuperAdmin", False):
            return qs
        entity_id = getattr(self.request, "entity_id", None)
        return qs.filter(EntityId=entity_id) if entity_id else qs.none()

    def perform_create(self, serializer):
        serializer.save(EntityId=self.request.entity_id, CreatedBy=self.request.user.UserId)

    def perform_destroy(self, instance):
        instance.Status = 4
        instance.save()


class SpeciesViewSet(FeatureGateMixin, EntityScopeInitialMixin, ModelViewSet):
    """Species tracking is part of the Starter+ ecosystem module — gated
    server-side (CLAUDE.md rule #6)."""
    required_feature = "ecosystem_basic"
    permission_classes = [IsAuthenticated]
    queryset = Species.objects.all()

    def get_serializer_class(self):
        return SpeciesListSerializer if self.action == "list" else SpeciesDetailSerializer

    def get_queryset(self):
        qs = Species.objects.filter(Status__lt=4)
        user = self.request.user
        if getattr(user, "IsSuperAdmin", False):
            return qs
        entity_id = getattr(self.request, "entity_id", None)
        return qs.filter(EntityId=entity_id) if entity_id else qs.none()

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        """GBIF taxonomy lookup. GET ?q=<common or scientific name> → top matches."""
        from .integrations import search_species
        return Response(search_species(request.query_params.get("q", "")))

    def perform_create(self, serializer):
        species = serializer.save(EntityId=self.request.entity_id, CreatedBy=self.request.user.UserId)
        # Best-effort GBIF/IUCN enrichment (never blocks create on external failure).
        from .integrations import enrich_species
        try:
            enrich_species(species)
        except Exception:  # defensive — integrations already swallow errors
            pass

    def perform_destroy(self, instance):
        instance.Status = 4
        instance.save()
