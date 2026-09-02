from django.urls import path

from .views import FoundingPartnerApplicationView

urlpatterns = [
    path(
        "founding-partner-applications/",
        FoundingPartnerApplicationView.as_view(),
        name="founding-partner-application",
    ),
]
