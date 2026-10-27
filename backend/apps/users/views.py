from typing import ClassVar

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from common.responses import error_response, success_response
from common.throttling import AuthRateThrottle, SensitiveRateThrottle

from . import services
from .cookies import (
    clear_refresh_cookie,
    origin_allowed,
    refresh_cookie,
    set_refresh_cookie,
)
from .models import User
from .permissions import IsOperational
from .serializers import (
    AccessTokenSerializer,
    ChangePasswordSerializer,
    EmptySerializer,
    LoginSerializer,
    LoginUserSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileDataSerializer,
    ProfileSerializer,
    RegisterDataSerializer,
    RegisteredUserSerializer,
    RegisterSerializer,
    TokenPairSerializer,
    UpdateProfileSerializer,
)
from .throttling import RecoveryIdentifierThrottle, RecoveryIPThrottle


def _envelope(name, data_serializer):
    return inline_serializer(
        name,
        {
            "success": serializers.BooleanField(),
            "message": serializers.CharField(),
            "data": data_serializer(),
        },
    )


_ERROR = inline_serializer(
    "AuthError",
    {
        "success": serializers.BooleanField(default=False),
        "message": serializers.CharField(),
        "errors": serializers.DictField(),
    },
)
_COMMON = {
    400: OpenApiResponse(_ERROR, description="Validation failed."),
    429: OpenApiResponse(_ERROR, description="Request rate limit exceeded."),
}


class _AuthBase(APIView):
    authentication_classes: ClassVar[list] = []
    permission_classes: ClassVar[list] = [AllowAny]  # the credential is in the body
    throttle_classes: ClassVar[list] = [AuthRateThrottle]


class LoginView(_AuthBase):
    @extend_schema(
        request=LoginSerializer,
        responses={
            200: _envelope("LoginResponse", TokenPairSerializer),
            401: OpenApiResponse(_ERROR, description="Invalid credentials."),
            403: OpenApiResponse(
                _ERROR,
                description="Correct credentials but account pending "
                "(code account_pending) or deactivated (code account_deactivated).",
            ),
            **_COMMON,
        },
        tags=["auth"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.authenticate_user(
            serializer.validated_data["username_or_phone"],
            serializer.validated_data["password"],
        )
        if user is None:
            return error_response(_("Invalid credentials."), status=401)
        # Only now (password verified) may the account status be revealed.
        services.ensure_can_login(user)
        refresh = RefreshToken.for_user(user)
        response = success_response(
            {
                "access": str(refresh.access_token),
                "user": LoginUserSerializer(user).data,
            },
            message=_("Login successful."),
        )
        set_refresh_cookie(response, str(refresh))
        return response


def _origin_rejected():
    return error_response(
        _("This request's origin is not allowed."),
        status=403,
        code="origin_rejected",
    )


class RefreshView(_AuthBase):
    @extend_schema(
        request=None,
        responses={
            200: _envelope("RefreshResponse", AccessTokenSerializer),
            401: OpenApiResponse(_ERROR, description="Token is invalid or expired."),
            403: OpenApiResponse(_ERROR, description="Origin not allowed."),
            **_COMMON,
        },
        tags=["auth"],
    )
    def post(self, request):
        if not origin_allowed(request):
            return _origin_rejected()
        raw = refresh_cookie(request)
        if not raw:
            return error_response(_("Token is invalid or expired."), status=401)
        try:
            tokens = services.rotate_refresh_token(raw)
        except TokenError:
            response = error_response(_("Token is invalid or expired."), status=401)
            clear_refresh_cookie(response)
            return response
        response = success_response(
            {"access": tokens["access"]},
            message=_("Token refreshed successfully."),
        )
        set_refresh_cookie(response, tokens["refresh"])
        return response


class LogoutView(_AuthBase):
    """Blacklist the refresh cookie. Missing or dead cookies still return 200."""

    @extend_schema(
        request=None,
        responses={
            200: _envelope("LogoutResponse", EmptySerializer),
            403: OpenApiResponse(_ERROR, description="Origin not allowed."),
            **_COMMON,
        },
        tags=["auth"],
    )
    def post(self, request):
        if not origin_allowed(request):
            return _origin_rejected()
        raw = refresh_cookie(request)
        if raw:
            try:
                services.logout(raw)
            except TokenError:
                pass
        response = success_response({}, message=_("Logged out successfully."))
        clear_refresh_cookie(response)
        return response


class MeView(APIView):
    """The caller's profile. Throttled with the global ``user`` scope."""

    permission_classes: ClassVar[list] = [IsOperational]

    @extend_schema(
        responses={
            200: _envelope("MeResponse", ProfileDataSerializer),
            401: OpenApiResponse(_ERROR, description="Not authenticated."),
            403: OpenApiResponse(
                _ERROR, description="Account deactivated (code account_deactivated)."
            ),
            429: OpenApiResponse(_ERROR, description="Request rate limit exceeded."),
        },
        tags=["auth"],
    )
    def get(self, request):
        return success_response({"user": ProfileSerializer(request.user).data})

    @extend_schema(
        request=UpdateProfileSerializer,
        responses={
            200: _envelope("UpdateMeResponse", ProfileDataSerializer),
            401: OpenApiResponse(_ERROR, description="Not authenticated."),
            403: OpenApiResponse(
                _ERROR, description="Account deactivated (code account_deactivated)."
            ),
            **_COMMON,
        },
        tags=["auth"],
    )
    def patch(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.update_profile(request.user, **serializer.validated_data)
        return success_response(
            {"user": ProfileSerializer(user).data}, message=_("Profile updated.")
        )


class ChangePasswordView(APIView):
    """The only way a user changes their own password (BR-9)."""

    permission_classes: ClassVar[list] = [IsOperational]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={
            200: _envelope("ChangePasswordResponse", EmptySerializer),
            401: OpenApiResponse(_ERROR, description="Not authenticated."),
            403: OpenApiResponse(
                _ERROR, description="Account deactivated (code account_deactivated)."
            ),
            **_COMMON,
        },
        tags=["auth"],
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.change_password(request.user, **serializer.validated_data)
        response = success_response(
            {}, message=_("Password changed. Please log in again.")
        )
        clear_refresh_cookie(response)
        return response


class _RecoveryBase(APIView):
    authentication_classes: ClassVar[list] = []
    permission_classes: ClassVar[list] = [AllowAny]
    throttle_classes: ClassVar[list] = [RecoveryIPThrottle]


class PasswordResetRequestView(_RecoveryBase):
    """Ask for a reset email. The answer never says whether the account exists."""

    throttle_classes: ClassVar[list] = [RecoveryIPThrottle, RecoveryIdentifierThrottle]

    @extend_schema(
        request=PasswordResetRequestSerializer,
        responses={200: _envelope("PasswordResetResponse", EmptySerializer), **_COMMON},
        tags=["auth"],
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.request_password_reset(serializer.validated_data["identifier"])
        return success_response(
            {},
            message=_(
                "If an email is on file for that account, a reset link has been sent."
            ),
        )


class PasswordResetConfirmView(_RecoveryBase):
    @extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={
            200: _envelope("PasswordResetConfirmResponse", EmptySerializer),
            **_COMMON,
        },
        tags=["auth"],
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.confirm_password_reset(**serializer.validated_data)
        response = success_response(
            {}, message=_("Password has been reset. Please log in.")
        )
        if refresh_cookie(request):
            clear_refresh_cookie(response)
        return response


class _RegisterView(APIView):
    """Public self-registration. Role comes from the subclass, never the request."""

    authentication_classes: ClassVar[list] = []
    permission_classes: ClassVar[list] = [AllowAny]
    throttle_classes: ClassVar[list] = [SensitiveRateThrottle]
    role: ClassVar[str]

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: _envelope("RegisterResponse", RegisterDataSerializer),
            **_COMMON,
        },
        tags=["auth"],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.register_account(role=self.role, **serializer.validated_data)
        if user.status == User.Status.PENDING_APPROVAL:
            message = _("Registration successful. Your account is pending approval.")
        else:
            message = _("Registration successful.")
        return success_response(
            {"user": RegisteredUserSerializer(user).data}, message=message, status=201
        )


class RegisterDriverView(_RegisterView):
    role = User.Role.DRIVER


class RegisterTraderView(_RegisterView):
    role = User.Role.TRADER


class RegisterClientView(_RegisterView):
    role = User.Role.CLIENT
