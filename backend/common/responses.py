from django.utils.translation import gettext_lazy as _
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

DEFAULT_SUCCESS_MESSAGE = _("Operation completed successfully.")


def success_response(
    data=None, message=DEFAULT_SUCCESS_MESSAGE, status=200, headers=None
):
    """Build ``{success, message, data}``. ``data`` is never null."""
    payload = {
        "success": True,
        "message": str(message),
        "data": {} if data is None else data,
    }
    return Response(payload, status=status, headers=headers)


def error_payload(message, errors=None, code=None):
    payload = {"success": False, "message": str(message), "errors": errors or {}}
    if code:
        payload["code"] = code
    return payload


def error_response(message, errors=None, status=400, headers=None, code=None):
    return Response(
        error_payload(message, errors, code), status=status, headers=headers
    )


class EnvelopeJSONRenderer(JSONRenderer):
    """Optional renderer: wraps plain 2xx payloads in the success envelope.

    Payloads that already carry a ``success`` key (from helpers, the exception
    handler or pagination) are left untouched.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get("response")
        wrap = (
            response is not None
            and 200 <= response.status_code < 300
            and response.status_code != 204
            and not (isinstance(data, dict) and "success" in data)
        )
        if wrap:
            data = {
                "success": True,
                "message": DEFAULT_SUCCESS_MESSAGE,
                "data": {} if data is None else data,
            }
        return super().render(data, accepted_media_type, renderer_context)
