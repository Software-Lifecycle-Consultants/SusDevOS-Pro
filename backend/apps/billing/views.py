from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.shared.views import EntityScopeInitialMixin

from .models import EntitySubscriptions, Plans
from .serializers import EntitySubscriptionsSerializer, PlansSerializer


class PlansListView(APIView):
    permission_classes = [AllowAny]  # pricing page is public

    def get(self, request):
        plans = Plans.objects.filter(IsPublic=True).order_by("SortOrder")
        return Response(PlansSerializer(plans, many=True).data)


class SubscriptionView(EntityScopeInitialMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # entity_id is re-resolved after DRF auth by EntityScopeInitialMixin
        # (handles the X-Entity-ID header, membership checks, and the fallback
        # to the user's own entity — the middleware leaves it None under JWT).
        entity_id = getattr(request, "entity_id", None)
        if not entity_id:
            return Response({"code": "no_entity", "detail": "No entity context."}, status=400)
        try:
            sub = EntitySubscriptions.objects.select_related("PlanId").get(
                EntityId_id=entity_id
            )
        except EntitySubscriptions.DoesNotExist:
            return Response({"code": "no_subscription",
                             "detail": "No subscription found for this entity."}, status=404)
        return Response(EntitySubscriptionsSerializer(sub).data)
