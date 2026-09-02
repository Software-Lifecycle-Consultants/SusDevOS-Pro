import logging

from django.conf import settings
from django.core.mail import EmailMessage
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.shared.views import EntityScopeInitialMixin

from .models import EntitySubscriptions, Plans
from .serializers import (
    EntitySubscriptionsSerializer,
    FoundingPartnerApplicationSerializer,
    PlansSerializer,
)

logger = logging.getLogger(__name__)


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
            return Response(
                {"code": "no_subscription", "detail": "No subscription found for this entity."},
                status=404,
            )
        return Response(EntitySubscriptionsSerializer(sub).data)


class FoundingPartnerApplicationView(APIView):
    """Public, rate-limited application endpoint for the Founding 10 programme."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "founding_application"

    def post(self, request):
        serializer = FoundingPartnerApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()

        try:
            EmailMessage(
                subject=f"Founding 10 application — {application.CompanyName}",
                body=(
                    f"Name: {application.FullName}\n"
                    f"Email: {application.Email}\n"
                    f"Company: {application.CompanyName}\n"
                    f"Role: {application.Role}\n"
                    f"Website: {application.Website or 'Not provided'}\n"
                    f"Use case: {application.UseCase}\n"
                    f"Expected users: {application.ExpectedUsers}\n"
                    f"Current tooling: {application.CurrentTooling or 'Not provided'}\n\n"
                    f"Live project:\n{application.LiveProject}\n\n"
                    f"Additional context:\n{application.Message or 'None'}\n"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[getattr(settings, "FOUNDING_APPLICATION_EMAIL", "hello@susdevos.com")],
                reply_to=[application.Email],
            ).send(fail_silently=False)
        except Exception:
            # The application is already safely stored. Email delivery failure
            # must not make a valid prospect resubmit or lose their information.
            logger.exception(
                "Founding Partner application notification failed for application %s",
                application.ApplicationId,
            )

        return Response(
            {
                "application_id": application.ApplicationId,
                "message": "Application received. We will respond within two business days.",
            },
            status=status.HTTP_201_CREATED,
        )
