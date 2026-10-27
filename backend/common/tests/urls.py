from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls import path
from rest_framework import exceptions, serializers
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from common.exceptions import ApplicationError, ConflictError
from common.pagination import StandardPagination
from common.responses import success_response
from common.throttling import (
    AuthRateThrottle,
    HealthRateThrottle,
    SensitiveRateThrottle,
)


class _S(serializers.Serializer):
    name = serializers.CharField()
    nested = serializers.ListField(child=serializers.IntegerField(), required=False)


def _raiser(exc):
    @api_view(["GET"])
    @permission_classes([AllowAny])
    def view(request):
        raise exc

    return view


@api_view(["POST"])
@permission_classes([AllowAny])
def validate(request):
    _S(data=request.data).is_valid(raise_exception=True)
    return success_response({})


@api_view(["GET"])
@permission_classes([AllowAny])
def ok(request):
    return success_response({"x": 1}, "Hello.")


@api_view(["GET"])
@permission_classes([AllowAny])
def empty(request):
    return success_response()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def protected(request):
    return success_response({})


@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def auth_view(request):
    return success_response({})


@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([SensitiveRateThrottle])
def sensitive_view(request):
    return success_response({})


@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([HealthRateThrottle])
def health_view(request):
    return success_response({})


class ListView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = ()

    def get(self, request):
        p = StandardPagination()
        page = p.paginate_queryset(list(range(250)), request)
        return p.get_paginated_response(page)


urlpatterns = [
    path("ok/", ok),
    path("empty/", empty),
    path("validate/", validate),
    path("protected/", protected),
    path("auth/", auth_view),
    path("sensitive/", sensitive_view),
    path("health/", health_view),
    path("list/", ListView.as_view()),
    path("e/notfound/", _raiser(exceptions.NotFound())),
    path("e/http404/", _raiser(Http404())),
    path("e/denied/", _raiser(exceptions.PermissionDenied())),
    path("e/django-denied/", _raiser(PermissionDenied())),
    path("e/notauth/", _raiser(exceptions.NotAuthenticated())),
    path("e/parse/", _raiser(exceptions.ParseError())),
    path("e/app/", _raiser(ApplicationError("Custom failure.", errors={"f": ["bad"]}))),
    path("e/conflict/", _raiser(ConflictError())),
    path("e/boom/", _raiser(RuntimeError("secret /etc/passwd stack"))),
]

handler404 = "common.views.not_found"
handler500 = "common.views.server_error"
