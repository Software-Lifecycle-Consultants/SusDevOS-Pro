from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.shared.views import TenantViewSetMixin

from .models import (
    Restorations,
    RestorationSpecies,
    TreeRemovalAffectedSpecies,
    TreeRemovalRemovedSpecies,
    TreeRemovals,
)
from .serializers import (
    RestorationsDetailSerializer,
    RestorationsListSerializer,
    RestorationSpeciesSerializer,
    TreeRemovalAffectedSpeciesSerializer,
    TreeRemovalsDetailSerializer,
    TreeRemovalsListSerializer,
    TreeRemovalSpeciesSerializer,
)


class TreeRemovalsViewSet(TenantViewSetMixin, ModelViewSet):
    queryset = TreeRemovals.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return TreeRemovalsListSerializer if self.action == "list" else TreeRemovalsDetailSerializer

    @action(detail=True, methods=["get", "post"], url_path="removed-species")
    def removed_species(self, request, pk=None):
        removal = self.get_object()
        if request.method == "GET":
            return Response(TreeRemovalSpeciesSerializer(
                removal.removed_species.all(), many=True).data)
        s = TreeRemovalSpeciesSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        obj = s.save(TreeRemovalId=removal)
        return Response(TreeRemovalSpeciesSerializer(obj).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch", "delete"],
            url_path=r"removed-species/(?P<record_id>\d+)")
    def removed_species_item(self, request, pk=None, record_id=None):
        removal = self.get_object()
        item = get_object_or_404(TreeRemovalRemovedSpecies, id=record_id, TreeRemovalId=removal)
        if request.method == "DELETE":
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        s = TreeRemovalSpeciesSerializer(item, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(TreeRemovalSpeciesSerializer(item).data)

    @action(detail=True, methods=["get", "post"], url_path="affected-species")
    def affected_species(self, request, pk=None):
        removal = self.get_object()
        if request.method == "GET":
            return Response(TreeRemovalAffectedSpeciesSerializer(
                removal.affected_species.all(), many=True).data)
        s = TreeRemovalAffectedSpeciesSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        obj = s.save(TreeRemovalId=removal)
        return Response(TreeRemovalAffectedSpeciesSerializer(obj).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch", "delete"],
            url_path=r"affected-species/(?P<record_id>\d+)")
    def affected_species_item(self, request, pk=None, record_id=None):
        removal = self.get_object()
        item = get_object_or_404(TreeRemovalAffectedSpecies, id=record_id, TreeRemovalId=removal)
        if request.method == "DELETE":
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        s = TreeRemovalAffectedSpeciesSerializer(item, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(TreeRemovalAffectedSpeciesSerializer(item).data)


class RestorationsViewSet(TenantViewSetMixin, ModelViewSet):
    queryset = Restorations.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return RestorationsListSerializer if self.action == "list" else RestorationsDetailSerializer

    @action(detail=True, methods=["get", "post"], url_path="species")
    def species(self, request, pk=None):
        restoration = self.get_object()
        if request.method == "GET":
            return Response(RestorationSpeciesSerializer(
                restoration.restoration_species.all(), many=True).data)
        s = RestorationSpeciesSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        obj = s.save(RestorationId=restoration)
        return Response(RestorationSpeciesSerializer(obj).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch", "delete"],
            url_path=r"species/(?P<record_id>\d+)")
    def species_item(self, request, pk=None, record_id=None):
        restoration = self.get_object()
        item = get_object_or_404(RestorationSpecies, id=record_id, RestorationId=restoration)
        if request.method == "DELETE":
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        s = RestorationSpeciesSerializer(item, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(RestorationSpeciesSerializer(item).data)
