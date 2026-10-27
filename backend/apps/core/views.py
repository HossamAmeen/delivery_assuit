from typing import ClassVar

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from common.responses import error_response, success_response
from common.throttling import HealthRateThrottle

from . import services

HEADER = "X-Health-Check-Token"
INVALID_PASSWORD = _("Invalid health check password.")


class _Envelope(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


class _Error(serializers.Serializer):
    success = serializers.BooleanField(default=False)
    message = serializers.CharField()
    errors = serializers.DictField()


_PARAMS = [
    OpenApiParameter(
        HEADER,
        str,
        OpenApiParameter.HEADER,
        required=False,
        description="Health password (preferred).",
    ),
    OpenApiParameter(
        "password",
        str,
        OpenApiParameter.QUERY,
        required=False,
        description="Health password fallback; appears in access logs.",
    ),
]
_COMMON = {
    403: OpenApiResponse(_Error, description="Invalid health check password."),
    429: OpenApiResponse(_Error, description="Request rate limit exceeded."),
}


class _HealthBase(APIView):
    authentication_classes: ClassVar[list] = []
    permission_classes: ClassVar[list] = [
        AllowAny
    ]  # access is controlled by the health password
    throttle_classes: ClassVar[list] = [HealthRateThrottle]

    def get(self, request):
        supplied = request.headers.get(HEADER) or request.query_params.get("password")
        if not services.password_is_valid(supplied):
            return error_response(INVALID_PASSWORD, status=403)
        return self.handle()

    def handle(self):  # pragma: no cover
        raise NotImplementedError


class HealthView(_HealthBase):
    @extend_schema(
        parameters=_PARAMS,
        responses={
            200: OpenApiResponse(_Envelope, description="Service is healthy."),
            **_COMMON,
        },
        tags=["health"],
    )
    def get(self, request):
        return super().get(request)

    def handle(self):
        return success_response({"status": "healthy"}, message=_("Service is healthy."))


class ReadyView(_HealthBase):
    @extend_schema(
        parameters=_PARAMS,
        responses={
            200: OpenApiResponse(_Envelope, description="Service is ready."),
            503: OpenApiResponse(_Error, description="Service is not ready."),
            **_COMMON,
        },
        tags=["health"],
    )
    def get(self, request):
        return super().get(request)

    def handle(self):
        checks = services.run_readiness_checks()
        failed = {k: v for k, v in checks.items() if v != services.OK}
        if failed:
            return error_response(
                _("Service is not ready."), {"checks": failed}, status=503
            )
        return success_response(
            {"status": "ready", "checks": checks}, message=_("Service is ready.")
        )
