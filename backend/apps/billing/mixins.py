"""
FeatureGateMixin — server-side feature gate enforcement.

Usage on any DRF view or ViewSet:

    class EmissionsViewSet(FeatureGateMixin, ModelViewSet):
        required_feature = "scope_3"
        ...

On access, checks whether the entity's current plan includes the feature.
Returns HTTP 402 with a structured error the frontend renders as an upgrade modal.

Gating is currently DISABLED platform-wide (settings.FEATURE_GATES_ENABLED, default
False): plans are sold on service and hosting tiers rather than per capability, so
this mixin is inert and every declared required_feature passes. The class, the 402
contract and its tests are kept intact so gating can be switched back on.

When enforcement is on: gates are server-side — never rely on frontend-only gating.
SuperAdmin bypasses all gates (SUPERADMIN_BYPASS).
"""
from rest_framework import status


class FeatureGateMixin:
    """
    Mix into a DRF APIView or ViewSet.
    Set ``required_feature`` to the feature key string (from PlanFeatures.FeatureKey).
    """
    required_feature: str | None = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)  # auth + perms first
        if self.required_feature:
            self._check_feature_gate(request)

    def _check_feature_gate(self, request):
        from apps.billing.services import feature_gates_enforced

        # Checked here rather than in initial() so the guard also covers any direct
        # caller of _check_feature_gate. The entity_id branch below never reaches
        # is_feature_enabled(), so short-circuiting there alone would not be enough.
        if not feature_gates_enforced():
            return

        if getattr(request.user, "IsSuperAdmin", False):  # SUPERADMIN_BYPASS
            return

        entity_id = getattr(request, "entity_id", None)
        if not entity_id:
            self._deny(self.required_feature)

        from apps.billing.services import is_feature_enabled
        if not is_feature_enabled(entity_id=entity_id, feature_key=self.required_feature):
            self._deny(self.required_feature)

    def _deny(self, feature_key: str):
        from apps.billing.services import get_upgrade_message
        raise FeatureGatedError(
            feature_key = feature_key,
            message     = get_upgrade_message(feature_key=feature_key),
        )


class FeatureGatedError(Exception):
    """Raised when a feature gate check fails. Caught by the custom exception handler."""
    status_code = status.HTTP_402_PAYMENT_REQUIRED

    def __init__(self, feature_key: str, message: str):
        self.feature_key = feature_key
        self.message = message
        super().__init__(message)
