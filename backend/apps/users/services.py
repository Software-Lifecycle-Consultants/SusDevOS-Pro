"""
Users service layer.

Signup and user-invitation orchestration. Both operations span multiple models
(Entity, User, UserRole, EntitySubscription, PasswordResetToken) and require
an atomic transaction — keeping this logic here means serializers only validate,
and the view only calls the service and issues tokens.
"""
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

# ── Self-service signup ───────────────────────────────────────────────────────

@transaction.atomic
def register_new_entity(
    *,
    first_name: str,
    last_name: str,
    email: str,
    company_name: str,
    password: str,
) -> "Users":  # noqa: F821 — forward reference for type hint
    """
    Create a new Entity + Admin User + Free plan subscription in one transaction.
    Returns the created User. Caller issues JWT tokens and returns the HTTP response.

    Creation order matters for FK integrity:
      Entity → User → UserRole → EntitySubscription
    Email is fire-and-forget inside try/except — a transient SMTP failure must
    not roll back account creation.
    """
    from apps.billing.models import EntitySubscriptions, Plans
    from apps.entities.models import Entities
    from apps.users.models import Roles, UserRoles, Users

    # 1. Entity
    entity = Entities.objects.create(EntityName=company_name)

    # 2. User — active immediately, no separate onboard step needed
    user = Users(
        email       = email,
        username    = _unique_username(email.split("@")[0]),
        FirstName   = first_name,
        LastName    = last_name,
        EntityId_id = entity.EntityId,
        is_active   = True,
    )
    user.set_password(password)
    user.save()

    # 3. Admin role for their own entity
    admin_role = Roles.objects.filter(RoleKey="admin", Status=1).first()
    if admin_role:
        UserRoles.objects.create(UserId=user, RoleId=admin_role)

    # 4. Free plan subscription
    free_plan = Plans.objects.filter(PlanKey="free").first()
    if free_plan:
        EntitySubscriptions.objects.create(
            EntityId_id = entity.EntityId,
            PlanId      = free_plan,
            Status      = "active",
        )

    # 5. Welcome email
    _send_welcome_email(email=email, first_name=first_name)

    return user


def _unique_username(base: str) -> str:
    """Derive a unique username from the email local-part."""
    import random
    import string

    from apps.users.models import Users

    candidate = base[:50]
    if not Users.objects.filter(username=candidate).exists():
        return candidate
    for _ in range(10):
        suffix = "".join(random.choices(string.digits, k=4))
        candidate = f"{base[:45]}_{suffix}"
        if not Users.objects.filter(username=candidate).exists():
            return candidate
    return f"{base[:40]}_{uuid.uuid4().hex[:8]}"


def _send_welcome_email(*, email: str, first_name: str) -> None:
    site_url = getattr(settings, "SITE_URL", "https://susdevos.com")
    try:
        send_mail(
            subject       = "Welcome to SusDevOS",
            message       = (
                f"Hi {first_name},\n\n"
                "Your SusDevOS account is ready. You're on the Free plan — "
                "upgrade any time from Settings → Billing.\n\n"
                f"{site_url}/dashboard"
            ),
            from_email    = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [email],
            fail_silently  = True,
        )
    except Exception:
        pass  # email failure must never abort account creation


# ── Admin-invited user creation ───────────────────────────────────────────────

@transaction.atomic
def invite_user(
    *,
    entity_id: int,
    email: str,
    username: str,
    first_name: str,
    last_name: str,
    designation: str | None = None,
    role_key: str,
) -> "Users":  # noqa: F821
    """
    Create an inactive user, assign a role, generate a one-time onboard token,
    and send the invitation email. Returns the created User.

    The user is created with a random unguessable password — they set their own
    via the onboard link.
    """
    import secrets as secrets_module

    from apps.users.models import PasswordResetTokens, Roles, UserRoles, Users

    user = Users.objects.create_user(
        password    = secrets_module.token_urlsafe(32),
        EntityId_id = entity_id,
        email       = email,
        username    = username,
        FirstName   = first_name,
        LastName    = last_name,
        Designation = designation,
    )

    role = Roles.objects.filter(RoleKey=role_key).first()
    if role:
        UserRoles.objects.create(UserId=user, RoleId=role)

    token = PasswordResetTokens.objects.create(
        UserId    = user,
        ExpiresAt = timezone.now() + timedelta(days=7),
    )

    onboard_url = f"{getattr(settings, 'ONBOARDING_URL', '/onboard')}?token={token.Token}"
    try:
        send_mail(
            subject       = "You've been invited to SusDevOS",
            message       = f"Set up your account:\n\n{onboard_url}",
            from_email    = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [email],
            fail_silently  = True,
        )
    except Exception:
        pass

    return user
