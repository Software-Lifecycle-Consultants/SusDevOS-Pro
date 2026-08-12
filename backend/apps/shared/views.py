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


def resolve_request_entity_id(request):
    """Re-resolve ``request.entity_id`` after DRF authentication.

    TenantQueryMiddleware runs before DRF authentication, so for JWT requests
    ``request.user`` is still anonymous when the middleware runs and it leaves
    ``request.entity_id`` = None.  This helper repeats the middleware's
    header/membership checks once DRF has authenticated the user, and must be
    called from ``initial()`` (after ``super().initial()``).

    Mutates ``request.entity_id`` in place.  Raises ``PermissionDenied`` when a
    non-SuperAdmin supplies an X-Entity-ID header for an entity they cannot
    access (a spoof attempt).
    """
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
        # Non-SA: verify they can access the requested entity (primary or
        # an EntityMembers grant — multi-entity users).  A header naming an
        # entity the user has no membership in is a spoof attempt: reject it
        # with 403 rather than silently returning an empty result set.  The
        # equivalent check in TenantQueryMiddleware never fires for JWT
        # requests because that middleware runs before DRF authentication.
        from apps.entities.services import user_can_access_entity
        if user_can_access_entity(user, header_id):
            request.entity_id = header_id
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                {"code": "forbidden_entity",
                 "detail": "You do not have access to this entity."}
            )
    elif not getattr(request, "entity_id", None):
        request.entity_id = getattr(user, "EntityId_id", None)


class EntityScopeInitialMixin:
    """Re-resolve ``request.entity_id`` after DRF authentication.

    Mix into any tenant-scoped APIView/ViewSet that reads ``request.entity_id``
    but cannot use the full :class:`TenantViewSetMixin` — e.g. viewsets whose
    model stores ``EntityId`` as a plain IntegerField (ecosystem.Ecosystem,
    ecosystem.Species) and views with a bespoke ``get_queryset``.  Without this,
    ``request.entity_id`` is None for JWT requests and tenant scoping silently
    fails (empty reads, NOT-NULL violations on create)."""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)  # runs DRF auth + perms
        resolve_request_entity_id(request)


class TenantViewSetMixin(EntityScopeInitialMixin):
    """
    Mixin for tenant-scoped ModelViewSets.

    The Django middleware runs before DRF authentication, so request.user may
    still be anonymous when the middleware sets request.entity_id.  entity_id is
    re-resolved in initial() (via EntityScopeInitialMixin) once DRF has
    authenticated the user.
    """

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
