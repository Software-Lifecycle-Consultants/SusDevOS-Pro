"""
Root URL configuration for SusDevOS.
All API routes are versioned under /api/.
OpenAPI schema at /api/schema/ (Swagger UI at /api/schema/swagger-ui/).
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),

    # OpenAPI schema
    path("api/schema/",            SpectacularAPIView.as_view(),         name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/",      SpectacularRedocView.as_view(url_name="schema"),   name="redoc"),

    # Application API routes
    path("api/auth/",          include("apps.users.urls.auth")),
    path("api/entities/",      include("apps.entities.urls")),
    path("api/users/",         include("apps.users.urls.users")),
    path("api/roles/",         include("apps.users.urls.roles")),
    path("api/modules/",       include("apps.users.urls.modules")),
    path("api/projects/",      include("apps.projects.urls")),
    path("api/land-parcels/",  include("apps.land.urls")),
    path("api/",               include("apps.ecosystem.urls")),      # /api/ecosystems/ + /api/species/
    path("api/",               include("apps.emissions.urls")),      # /api/emissions/ + /api/gwp-datasets/ etc.
    path("api/",               include("apps.restorations.urls")),   # /api/tree-removals/ + /api/restorations/
    path("api/shared/",        include("apps.shared.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/blog/",          include("apps.blog.urls")),
    path("api/reports/",       include("apps.reports.urls")),
    path("api/billing/",       include("apps.billing.urls")),

    # Public blog endpoint (no auth)
    path("api/public/",        include("apps.blog.urls_public")),

    # Integration endpoints
    path("api/integrations/",  include("apps.shared.urls_integrations")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
