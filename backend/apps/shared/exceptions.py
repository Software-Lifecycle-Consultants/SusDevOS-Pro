"""
Custom DRF exception handler.
Wraps all error responses in a consistent envelope:
  { "code": "...", "detail": "...", "errors": {...} }

Also handles FeatureGatedError → HTTP 402 with upgrade modal payload.
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # Handle feature gate before DRF exception_handler (which doesn't know it)
    try:
        from apps.billing.mixins import FeatureGatedError
        if isinstance(exc, FeatureGatedError):
            return Response(
                {
                    "code":        "feature_gated",
                    "feature":     exc.feature_key,
                    "detail":      exc.message,
                    "upgrade_url": "/pricing",
                },
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )
    except ImportError:
        pass
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data

        # Already formatted
        if isinstance(data, dict) and "code" in data:
            return response

        # DRF validation errors arrive as dicts of field: [error]
        if isinstance(data, dict):
            code = data.pop("detail", None)
            if hasattr(code, "code"):
                error_code = code.code
                detail = str(code)
            else:
                error_code = "validation_error"
                detail = "Invalid input."

            response.data = {
                "code":   error_code,
                "detail": detail,
                "errors": data if data else {},
            }
        elif isinstance(data, list):
            response.data = {
                "code":   "error",
                "detail": str(data[0]) if data else "An error occurred.",
                "errors": {},
            }

    return response
