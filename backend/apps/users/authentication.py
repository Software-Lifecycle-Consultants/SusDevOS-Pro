"""
Custom JWT authentication that checks the RevokedTokens table before accepting
an access token. Also provides helpers for issuing tokens with the HttpOnly
refresh cookie pattern.
"""
from datetime import timedelta

from django.conf import settings

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken


class RevokedTokenJWTAuthentication(JWTAuthentication):
    """Extends SimpleJWT to reject tokens whose Jti is in RevokedTokens."""

    def get_validated_token(self, raw_token):
        validated = super().get_validated_token(raw_token)
        jti = validated.get("jti")
        if jti:
            import uuid

            from apps.users.models import RevokedTokens
            try:
                jti_uuid = uuid.UUID(jti)
            except ValueError:
                raise InvalidToken("Token has an invalid jti claim.")
            if RevokedTokens.objects.filter(Jti=jti_uuid).exists():
                raise InvalidToken("Token has been revoked.")
        return validated


def issue_tokens(user):
    """
    Returns (access_token_str, refresh_token_obj).
    Caller is responsible for setting the HttpOnly cookie from the refresh token.
    """
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), refresh


def set_refresh_cookie(response, refresh_token):
    """Attaches the refresh token as an HttpOnly, SameSite=Lax cookie."""
    max_age = int(
        settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME", timedelta(days=7)).total_seconds()
    )
    response.set_cookie(
        key="refresh_token",
        value=str(refresh_token),
        max_age=max_age,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        path="/api/auth/refresh",
    )


def clear_refresh_cookie(response):
    response.delete_cookie("refresh_token", path="/api/auth/refresh")
