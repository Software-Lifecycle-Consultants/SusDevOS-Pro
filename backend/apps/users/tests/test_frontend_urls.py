"""
The email-link settings must name routes the frontend actually serves.

ONBOARDING_URL pointed at /onboarding for the life of the project while the Next.js
route has always been /onboard. Nothing server-side could detect it: the email sends,
the token is valid, and the recipient lands on a 404 unable to finish onboarding. The
first person to notice would be a locked-out customer.

The backend image does not contain the frontend tree, so these tests assert against an
explicit list of public routes and additionally cross-check the filesystem when it is
available (local checkout, CI). Keep PUBLIC_ROUTES in step with
frontend/src/app/(public)/ — the cross-check fails if they drift.
"""
from pathlib import Path

from django.conf import settings

# Directories under frontend/src/app/(public)/ that contain a page.tsx.
PUBLIC_ROUTES = {
    "forgot-password",
    "login",
    "onboard",
    "register",
    "reset-password",
}

FRONTEND_PUBLIC_DIR = (
    Path(settings.BASE_DIR).parent / "frontend" / "src" / "app" / "(public)"
)


def _route_of(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def test_onboarding_url_matches_a_real_frontend_route():
    route = _route_of(settings.ONBOARDING_URL)
    assert route in PUBLIC_ROUTES, (
        f"ONBOARDING_URL points at '/{route}', which the frontend does not serve. "
        f"Public routes: {sorted(PUBLIC_ROUTES)}. An onboarding email built from this "
        f"setting would send a valid token to a 404."
    )


def test_password_reset_url_matches_a_real_frontend_route():
    route = _route_of(settings.PASSWORD_RESET_URL)
    assert route in PUBLIC_ROUTES, (
        f"PASSWORD_RESET_URL points at '/{route}', which the frontend does not serve. "
        f"Public routes: {sorted(PUBLIC_ROUTES)}."
    )


def test_email_link_settings_are_absolute_urls():
    """A relative link in an email is unclickable."""
    for name in ("ONBOARDING_URL", "PASSWORD_RESET_URL", "FRONTEND_URL"):
        value = getattr(settings, name)
        assert value.startswith(("http://", "https://")), f"{name} is not absolute: {value}"


def test_public_routes_list_matches_the_frontend_tree():
    """Keeps PUBLIC_ROUTES honest wherever the frontend is checked out.

    Skipped in the backend-only container, where the frontend tree is absent — the
    two tests above still hold the settings to the list either way.
    """
    if not FRONTEND_PUBLIC_DIR.is_dir():
        return

    actual = {
        child.name
        for child in FRONTEND_PUBLIC_DIR.iterdir()
        if child.is_dir() and any(child.glob("page.*"))
    }
    assert actual == PUBLIC_ROUTES, (
        f"PUBLIC_ROUTES has drifted from frontend/src/app/(public)/. "
        f"On disk: {sorted(actual)}. In this file: {sorted(PUBLIC_ROUTES)}."
    )
