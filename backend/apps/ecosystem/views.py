from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import Ecosystem, Species
from .serializers import (
    EcosystemDetailSerializer, EcosystemListSerializer,
    SpeciesDetailSerializer, SpeciesListSerializer,
)


class EcosystemViewSet(ModelViewSet):
    """Ecosystem uses IntegerField for EntityId — uses a custom queryset filter."""
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


class SpeciesViewSet(ModelViewSet):
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

    def perform_create(self, serializer):
        serializer.save(EntityId=self.request.entity_id, CreatedBy=self.request.user.UserId)

    def perform_destroy(self, instance):
        instance.Status = 4
        instance.save()
