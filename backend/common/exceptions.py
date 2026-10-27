from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException


class ApplicationError(APIException):
    """Base class for domain errors. Subclass and set status/message/code."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Request could not be completed.")
    default_code = "application_error"
    # Optional machine-readable code exposed in the error body as ``code``.
    public_code = None

    def __init__(self, message=None, errors=None, code=None, status_code=None):
        super().__init__(detail=message, code=code)
        self.errors = errors or {}
        if status_code is not None:
            self.status_code = status_code


class ConflictError(ApplicationError):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _("Conflict with the current state of the resource.")
    default_code = "conflict"
