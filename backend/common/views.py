from rest_framework import status

from .exception_handler import MESSAGES
from .responses import error_payload


def _json(request, code):
    from django.http import JsonResponse

    return JsonResponse(error_payload(MESSAGES[code]), status=code)


def not_found(request, exception=None):
    """handler404: unknown routes use the standard error envelope."""
    return _json(request, status.HTTP_404_NOT_FOUND)


def server_error(request):
    """handler500: never leaks internals."""
    return _json(request, status.HTTP_500_INTERNAL_SERVER_ERROR)


__all__ = ["not_found", "server_error"]
