"""
TenantViewSetMixin — tenant scoping + soft-delete for every domain ViewSet.

Usage:
    class FooViewSet(TenantViewSetMixin, ModelViewSet):
        queryset = Foo.objects.all()
        serializer_class = FooSerializer

For models where EntityId is an IntegerField (ecosystem.Ecosystem, ecosystem.Species):
    override get_queryset and use filter(EntityId=entity_id) directly.
"""
from rest_framework.response import Response
from rest_framework import status


class TenantViewSetMixin:
    """
    Mixin for tenant-scoped ModelViewSets.

    The Django middleware runs before DRF authentication, so request.user may
    still be anonymous when the middleware sets request.entity_id.  We
    re-resolve entity_id in initial() once DRF has authenticated the user.
    """

    def initial(self, request, *args, **kwargs):
        """Re-resolve entity_id after DRF authentication has set request.user."""
        super().initial(request, *args, **kwargs)  # runs DRF auth + perms
        user = request.user
        header_id = request.META.get("HTTP_X_ENTITY_ID")
        if header_id:
            try:
                header_id = int(header_id)
            except (ValueError, TypeError):
                header_id = None
        if header_id and getattr(user, "IsSuperAdmin", False):  # SUPERADMIN_BYPASS
            request.entity_id = header_id
        elif header_id:
            # Non-SA: verify they belong to the requested entity
            if getattr(user, "EntityId_id", None) == header_id:
                request.entity_id = header_id
            # else leave as-is (middleware already denied or set correctly)
        elif not getattr(request, "entity_id", None):
            request.entity_id = getattr(user, "EntityId_id", None)

    def get_queryset(self):
        qs = super().get_queryset().filter(Status__lt=4)
        user = self.request.user
        if getattr(user, "IsSuperAdmin", False):  # SUPERADMIN_BYPASS
            return qs
        entity_id = getattr(self.request, "entity_id", None)
        if not entity_id:
            return qs.none()
        return qs.filter(EntityId=entity_id)

    def perform_create(self, serializer):
        instance = serializer.save(
            EntityId_id=self.request.entity_id,
            CreatedBy=self.request.user.UserId,
        )
        self._audit("Create", instance)
        return instance

    def perform_update(self, serializer):
        instance = serializer.save(UpdatedBy=self.request.user.UserId)
        self._audit("Update", instance)
        return instance

    def perform_destroy(self, instance):
        instance.Status = 4
        instance.save()
        self._audit("Delete", instance)

    def _audit(self, action, instance):
        from apps.shared.audit import audit_log
        audit_log(
            action=action,
            table_name=getattr(instance._meta, "db_table", None),
            record_id=getattr(instance, "pk", None),
            description=f"{action} {instance.__class__.__name__} #{getattr(instance, 'pk', '?')}",
            request=self.request,
        )
