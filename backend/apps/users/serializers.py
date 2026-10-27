from typing import ClassVar

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from . import services
from .models import User
from .phone import is_valid_phone, normalize_phone


class LoginSerializer(serializers.Serializer):
    username_or_phone = serializers.CharField(max_length=150)
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=128
    )


class LoginUserSerializer(serializers.Serializer):
    """Output only: the summary the client needs to route to the role's home."""

    id = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)


class TokenPairSerializer(serializers.Serializer):
    """Login body. The refresh token is a cookie, not a field (VULN-012)."""

    access = serializers.CharField()
    user = LoginUserSerializer()


class AccessTokenSerializer(serializers.Serializer):
    access = serializers.CharField()


class EmptySerializer(serializers.Serializer):
    pass


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=128
    )
    new_password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=128
    )


class PasswordResetRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=254)


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=256, trim_whitespace=False)
    new_password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=128
    )


class UpdateProfileSerializer(serializers.Serializer):
    """PATCH /auth/me/. Role, status, and username are refused, not ignored."""

    FORBIDDEN: ClassVar[tuple] = ("role", "status", "username")

    full_name = serializers.CharField(min_length=2, max_length=255, required=False)
    phone = serializers.CharField(max_length=32, required=False)
    email = serializers.EmailField(required=False, allow_blank=True, max_length=254)

    def to_internal_value(self, data):
        forbidden = {
            key: [_("You cannot change this field.")]
            for key in self.FORBIDDEN
            if key in data
        }
        try:
            attrs = super().to_internal_value(data)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError({**exc.detail, **forbidden}) from exc
        if forbidden:
            raise serializers.ValidationError(forbidden)
        return attrs

    def validate_phone(self, value):
        if not is_valid_phone(value):
            raise serializers.ValidationError(
                _("Enter a valid phone number (8 to 15 digits).")
            )
        phone = normalize_phone(value)
        if services.phone_exists(phone, exclude_pk=self.instance.pk):
            raise serializers.ValidationError(services.PHONE_TAKEN)
        return phone

    def validate_email(self, value):
        value = value.strip().lower()
        if value and services.email_exists(value, exclude_pk=self.instance.pk):
            raise serializers.ValidationError(services.EMAIL_TAKEN)
        return value


class ProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    phone = serializers.CharField(allow_null=True)
    username = serializers.CharField(allow_null=True)
    email = serializers.CharField(allow_blank=True)
    role = serializers.CharField()
    status = serializers.CharField()
    rejection_reason = serializers.CharField(allow_blank=True)


class ProfileDataSerializer(serializers.Serializer):
    user = ProfileSerializer()


class RegisterSerializer(serializers.Serializer):
    """Input only. Role and status are deliberately not fields (never from the body)."""

    full_name = serializers.CharField(min_length=2, max_length=255)
    phone = serializers.CharField(max_length=32)
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=128
    )
    email = serializers.EmailField(required=False, allow_blank=True, max_length=254)

    def validate_phone(self, value):
        if not is_valid_phone(value):
            raise serializers.ValidationError(
                _("Enter a valid phone number (8 to 15 digits).")
            )
        phone = normalize_phone(value)
        if services.phone_exists(phone):
            raise serializers.ValidationError(services.PHONE_TAKEN)
        return phone

    def validate_email(self, value):
        if value and services.email_exists(value):
            raise serializers.ValidationError(
                _("A user with this email already exists.")
            )
        return value

    def validate(self, attrs):
        candidate = User(
            full_name=attrs["full_name"],
            phone=attrs["phone"],
            email=attrs.get("email", ""),
        )
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs


class RegisteredUserSerializer(serializers.Serializer):
    """Output only: registration summary."""

    id = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)


class RegisterDataSerializer(serializers.Serializer):
    user = RegisteredUserSerializer()
