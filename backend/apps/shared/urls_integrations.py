"""Integration lookup endpoints (Companies House, etc.) — stubs for API layer."""
from django.urls import path
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class CompaniesHouseLookupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        POST /api/integrations/companies-house/lookup/
        Body: { "company_number": "12345678" } or { "query": "Company Name" }
        Calls Companies House API and returns candidate matches.
        """
        from django.conf import settings
        import requests
        query = request.data.get("query")
        number = request.data.get("company_number")
        api_key = getattr(settings, "COMPANIES_HOUSE_API_KEY", "")
        if not api_key:
            return Response({"code": "not_configured",
                             "detail": "Companies House API key not configured."}, status=503)
        if number:
            resp = requests.get(
                f"https://api.company-information.service.gov.uk/company/{number}",
                auth=(api_key, ""), timeout=8,
            )
        elif query:
            resp = requests.get(
                "https://api.company-information.service.gov.uk/search/companies",
                params={"q": query}, auth=(api_key, ""), timeout=8,
            )
        else:
            return Response({"code": "required",
                             "detail": "Provide company_number or query."}, status=400)
        if resp.status_code == 404:
            return Response({"code": "not_found", "detail": "Company not found."}, status=404)
        return Response(resp.json())


urlpatterns = [
    path("companies-house/lookup/",
         CompaniesHouseLookupView.as_view(),
         name="companies-house-lookup"),
]
