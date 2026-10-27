from typing import ClassVar

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView

from common.responses import success_response

from . import admin_services
from .admin_filters import UserFilter
from .admin_serializers import (
    CreateUserSerializer,
    ManagedUserDataSerializer,
    ManagedUserSerializer,
    RejectSerializer,
    UpdateUserSerializer,
    UserListSerializer,
)
from .models import User
from .permissions import IsAdminOrManager
from .views import _COMMON, _ERROR, _envelope


def _managed(user):
    return {"user": ManagedUserSerializer(user).data}


class _StaffBase(APIView):
    """Admin or Manager only. Throttled with the global ``user`` scope."""

    permission_classes: ClassVar[list] = [IsAdminOrManager]

    def target(self, pk) -> User:
        return get_object_or_404(User.objects, pk=pk)


_RESPONSES = {
    200: _envelope("ManagedUserResponse", ManagedUserDataSerializer),
    401: OpenApiResponse(_ERROR, description="Not authenticated."),
    403: OpenApiResponse(
        _ERROR, description="Not staff, or a Manager targeting an Admin."
    ),
    404: OpenApiResponse(_ERROR, description="Unknown or deleted user."),
    **_COMMON,
}


class ApproveView(_StaffBase):
    @extend_schema(request=None, responses=_RESPONSES, tags=["users"])
    def post(self, request, pk):
        user = admin_services.approve_account(self.target(pk), request.user)
        return success_response(_managed(user), message=_("User approved."))


class RejectView(_StaffBase):
    @extend_schema(request=RejectSerializer, responses=_RESPONSES, tags=["users"])
    def post(self, request, pk):
        serializer = RejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data["reason"].strip()
        user = admin_services.reject_account(self.target(pk), request.user, reason)
        return success_response(_managed(user), message=_("User rejected."))


class ActivateView(_StaffBase):
    @extend_schema(request=None, responses=_RESPONSES, tags=["users"])
    def post(self, request, pk):
        user = admin_services.activate_account(self.target(pk), request.user)
        return success_response(_managed(user), message=_("User activated."))


class DeactivateView(_StaffBase):
    @extend_schema(request=None, responses=_RESPONSES, tags=["users"])
    def post(self, request, pk):
        user = admin_services.deactivate_account(self.target(pk), request.user)
        return success_response(_managed(user), message=_("User deactivated."))


class UserListView(ListAPIView):
    """Every live user, newest first. A Manager sees Admin rows too."""

    permission_classes: ClassVar[list] = [IsAdminOrManager]
    serializer_class = UserListSerializer
    filterset_class = UserFilter
    queryset = User.objects.order_by("-id")

    @extend_schema(
        responses={
            401: OpenApiResponse(_ERROR, description="Not authenticated."),
            403: OpenApiResponse(_ERROR, description="Not Admin or Manager."),
            **_COMMON,
        },
        tags=["users"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=CreateUserSerializer,
        responses={201: _envelope("CreatedUserResponse", ManagedUserDataSerializer)}
        | {k: v for k, v in _RESPONSES.items() if k != 200},
        tags=["users"],
    )
    def post(self, request):
        # Refuse an Admin role from a Manager before any other validation.
        admin_services.ensure_can_assign_role(request.user, request.data.get("role"))
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = admin_services.create_user(request.user, **serializer.validated_data)
        return success_response(_managed(user), message=_("User created."), status=201)


class UserDetailView(_StaffBase):
    @extend_schema(responses=_RESPONSES, tags=["users"])
    def get(self, request, pk):
        return success_response(_managed(self.target(pk)))

    @extend_schema(request=UpdateUserSerializer, responses=_RESPONSES, tags=["users"])
    def patch(self, request, pk):
        target = self.target(pk)
        admin_services.ensure_can_manage(request.user, target)
        admin_services.ensure_can_assign_role(request.user, request.data.get("role"))
        serializer = UpdateUserSerializer(target, data=request.data)
        serializer.is_valid(raise_exception=True)
        user = admin_services.update_user(
            request.user, target, **serializer.validated_data
        )
        return success_response(_managed(user), message=_("User updated."))

    @extend_schema(request=None, responses=_RESPONSES, tags=["users"])
    def delete(self, request, pk):
        admin_services.delete_user(request.user, self.target(pk))
        return success_response({}, message=_("User deleted."))
