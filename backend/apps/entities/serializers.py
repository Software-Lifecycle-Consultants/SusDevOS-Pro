import hashlib
import secrets

from django.conf import settings
from rest_framework import serializers

from apps.shared.models import Contacts, Documents, EntityApiKeys, Locations
from .models import (
    Entities,
    EntityApiKeysIntermediary,
    EntityContacts,
    EntityDocuments,
    EntityLocations,
    RelatedEntities,
)


class EntitiesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entities
        fields = (
            "EntityId", "EntityName", "EntityType", "RegistrationNumber",
            "Country", "BaseCurrency", "Status", "CreatedAt",
        )


class EntitiesDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entities
        fields = "__all__"
        read_only_fields = ("EntityId", "CreatedAt", "UpdatedAt", "CreatedBy", "UpdatedBy")


class EntityCreateSerializer(serializers.ModelSerializer):
    """SA-only: creates an entity + an initial admin user."""
    initial_admin_email    = serializers.EmailField(write_only=True)
    initial_admin_username = serializers.CharField(write_only=True, max_length=150)

    class Meta:
        model = Entities
        fields = (
            "EntityName", "EntityType", "RegistrationNumber", "VATNumber",
            "AddressLine1", "AddressLine2", "City", "PostCode", "Country",
            "BaseCurrency", "FiscalYearEndMonth",
            "initial_admin_email", "initial_admin_username",
        )

    def create(self, validated_data):
        admin_email    = validated_data.pop("initial_admin_email")
        admin_username = validated_data.pop("initial_admin_username")

        entity = Entities.objects.create(**validated_data)

        # Create the initial admin user (inactive until onboard)
        from apps.users.models import Roles, UserRoles, Users, PasswordResetTokens
        from django.utils import timezone
        from datetime import timedelta
        from django.core.mail import send_mail

        user = Users.objects.create_user(
            email=admin_email,
            username=admin_username,
            password=secrets.token_urlsafe(32),  # random; replaced on onboard
            EntityId=entity,
        )
        admin_role = Roles.objects.filter(RoleKey="admin").first()
        if admin_role:
            UserRoles.objects.create(UserId=user, RoleId=admin_role)

        token = PasswordResetTokens.objects.create(
            UserId=user,
            ExpiresAt=timezone.now() + timedelta(days=7),
        )
        onboard_url = f"{settings.ONBOARDING_URL}?token={token.Token}"
        send_mail(
            subject="You've been added to SusDevOS",
            message=f"Set up your account:\n\n{onboard_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=True,
        )

        # Assign Free plan subscription
        from apps.billing.models import EntitySubscriptions, Plans
        free_plan = Plans.objects.filter(PlanKey="free").first()
        if free_plan:
            EntitySubscriptions.objects.get_or_create(
                EntityId=entity,
                defaults={"PlanId": free_plan, "Status": "active", "BillingInterval": "monthly"},
            )

        return entity


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locations
        fields = ("LocationId", "Title", "City", "Country", "Remarks", "GPSCoordinates")
        read_only_fields = ("LocationId",)


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contacts
        fields = (
            "ContactId", "Name", "Designation", "Email", "PhoneNumber",
            "ModuleKey", "AddressLine1", "City", "PostCode", "Country",
        )
        read_only_fields = ("ContactId",)


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documents
        fields = ("DocumentId", "DocTitle", "DocPath", "DocType", "ModuleKey", "Description")
        read_only_fields = ("DocumentId",)


class ApiKeyCreateResponseSerializer(serializers.Serializer):
    """Returned once on key creation — raw key is never stored."""
    ApiKeyId   = serializers.IntegerField()
    KeyPrefix  = serializers.CharField()
    RawKey     = serializers.CharField()
    ExpiryDate = serializers.DateTimeField(allow_null=True)


class ApiKeyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityApiKeys
        fields = ("ApiKeyId", "KeyPrefix", "ExpiryDate", "AuthorizedByFor", "Status", "CreatedAt")
