import logging

from django.core.exceptions import (
    PermissionDenied,
    RequestDataTooBig,
    SuspiciousOperation,
)
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from .exceptions import ApplicationError
from .responses import error_payload

logger = logging.getLogger(__name__)

MESSAGES = {
    status.HTTP_400_BAD_REQUEST: _("Validation failed."),
    status.HTTP_401_UNAUTHORIZED: _(
        "Authentication credentials were not provided or are invalid."
    ),
    status.HTTP_403_FORBIDDEN: _("You do not have permission to perform this action."),
    status.HTTP_404_NOT_FOUND: _("Resource not found."),
    status.HTTP_405_METHOD_NOT_ALLOWED: _("Method not allowed."),
    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: _("Request body is too large."),
    status.HTTP_429_TOO_MANY_REQUESTS: _("Request rate limit exceeded."),
    status.HTTP_500_INTERNAL_SERVER_ERROR: _("An unexpected error occurred."),
}


def _normalize(detail):
    """Turn DRF error details into ``{field: [messages]}``."""
    if isinstance(detail, dict):
        return {str(k): _as_list(v) for k, v in detail.items()}
    return {"non_field_errors": _as_list(detail)}


def _as_list(value):
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            out.extend(
                _as_list(item) if isinstance(item, (list, tuple)) else [_flat(item)]
            )
        return out
    return [_flat(value)]


def _flat(value):
    if isinstance(value, dict):
        return {str(k): _as_list(v) for k, v in value.items()}
    return str(value)


def exception_handler(exc, context):
    """DRF EXCEPTION_HANDLER returning ``{success: false, message, errors}``."""
    if isinstance(exc, RequestDataTooBig):
        return Response(
            error_payload(MESSAGES[status.HTTP_413_REQUEST_ENTITY_TOO_LARGE]),
            status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )
    if isinstance(exc, SuspiciousOperation):
        exc = exceptions.ValidationError()
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    if isinstance(exc, exceptions.APIException):
        response = drf_exception_handler(exc, context)
        if response is None:  # pragma: no cover - defensive
            return _server_error(exc, context)
        code = response.status_code
        if isinstance(exc, ApplicationError):
            message = str(exc.detail)
            errors = exc.errors
        elif isinstance(exc, exceptions.ValidationError):
            message = MESSAGES[status.HTTP_400_BAD_REQUEST]
            errors = _normalize(exc.detail)
        elif isinstance(exc, exceptions.ParseError):
            message = MESSAGES[status.HTTP_400_BAD_REQUEST]
            errors = {"non_field_errors": [str(_("Invalid JSON."))]}
        elif code in MESSAGES:
            message = MESSAGES[code]
            errors = {}
        else:
            message = str(exc.detail)
            errors = {}
        # Use the handler's headers (WWW-Authenticate, Retry-After) but a new body.
        headers = {
            k: v
            for k, v in response.items()
            if k in ("WWW-Authenticate", "Retry-After")
        }
        public_code = getattr(exc, "public_code", None)
        return Response(
            error_payload(message, errors, public_code), status=code, headers=headers
        )

    return _server_error(exc, context)


def _server_error(exc, context):
    logger.error(
        "Unhandled exception in %s",
        context.get("view").__class__.__name__ if context else "unknown",
        exc_info=exc,
    )
    return Response(
        error_payload(MESSAGES[status.HTTP_500_INTERNAL_SERVER_ERROR]),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
