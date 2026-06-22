from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Notifications
from .serializers import NotificationsSerializer


class NotificationsViewSet(ModelViewSet):
    serializer_class = NotificationsSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        entity_id = getattr(self.request, "entity_id", None)
        qs = Notifications.objects.filter(UserId=user)
        if entity_id:
            qs = qs.filter(EntityId_id=entity_id)
        if self.request.query_params.get("unread"):
            qs = qs.filter(IsRead=False)
        return qs.order_by("-CreatedAt")

    def partial_update(self, request, *args, **kwargs):
        """PATCH {id}/ — only IsRead can be updated."""
        instance = self.get_object()
        instance.IsRead = request.data.get("IsRead", instance.IsRead)
        instance.save()
        return Response(NotificationsSerializer(instance).data)

    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        self.get_queryset().filter(IsRead=False).update(IsRead=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
