"""
TenantQueryMiddleware — entity-scoped multi-tenancy.

Attaches request.entity_id from:
  1. X-Entity-ID header (multi-entity users: admins, consultants)
  2. User's default EntityId_id

SuperAdmin may pass any EntityId. Others restricted to their own entity.
"""
import logging

from django.http import JsonResponse

logger = logging.getLogger(__name__)


class TenantQueryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not hasattr(request, "user") or not request.user.is_authenticated:
            request.entity_id = None
            return self.get_response(request)

        user = request.user
        requested_entity_id = request.headers.get("X-Entity-ID")

        if requested_entity_id:
            try:
                requested_entity_id = int(requested_entity_id)
            except (ValueError, TypeError):
                return JsonResponse(
                    {"code": "invalid_entity_id", "detail": "X-Entity-ID must be an integer."},
                    status=400,
                )
            if getattr(user, "is_superadmin", False):
                request.entity_id = requested_entity_id
            elif not self._user_belongs_to_entity(user, requested_entity_id):
                return JsonResponse(
                    {"code": "forbidden_entity", "detail": "You do not have access to this entity."},
                    status=403,
                )
            else:
                request.entity_id = requested_entity_id
        else:
            request.entity_id = getattr(user, "EntityId_id", None)

        return self.get_response(request)

    def _user_belongs_to_entity(self, user, entity_id: int) -> bool:
        # Primary entity or an EntityMembers grant (multi-entity users).
        from apps.entities.services import user_can_access_entity
        return user_can_access_entity(user, entity_id)
