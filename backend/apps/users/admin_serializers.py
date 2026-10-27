from typing import ClassVar

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from . import admin_services
from .models import AccountAction, User
from .phone import is_valid_phone, normalize_phone
from .services import EMAIL_TAKEN, PHONE_TAKEN, email_exists, phone_exists


class LastActionSerializer(serializers.ModelSerializer):
    actor_id = serializers.IntegerField(read_only=True)
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = AccountAction
        fields = ("action", "reason", "actor_id", "actor_name", "created_at")

    def get_actor_name(self, obj) -> str:
        return obj.actor.full_name if obj.actor_id else ""


class ManagedUserSerializer(serializers.ModelSerializer):
    """Profile plus the latest account action. Never exposes secrets."""

    last_action = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "full_name",
            "phone",
            "username",
            "email",
            "role",
            "status",
            "rejection_reason",
            "last_action",
        )
        read_only_fields = fields

    def get_last_action(self, obj):
        action = (
            AccountAction.objects.filter(user=obj)
            .select_related("actor")
            .order_by("-id")
            .first()
        )
        return LastActionSerializer(action).data if action else None


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "full_name", "phone", "username", "email", "role", "status")
        read_only_fields = fields


class ManagedUserDataSerializer(serializers.Serializer):
    user = ManagedUserSerializer()


class RejectSerializer(serializers.Serializer):
    reason = serializers.CharField(
        max_length=500, required=False, allow_blank=True, default=""
    )


class _UserWriteSerializer(serializers.Serializer):
    """Shared rules for POST and PATCH /users/. Status and staff flags are refused."""

    FORBIDDEN: ClassVar[tuple] = ("status", "is_staff", "is_superuser")

    full_name = serializers.CharField(min_length=2, max_length=255)
    phone = serializers.CharField(max_length=32)
    username = serializers.CharField(max_length=150, allow_blank=True)
    email = serializers.EmailField(allow_blank=True, max_length=254)
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=128
    )
    role = serializers.ChoiceField(choices=User.Role.choices)

    def _exclude_pk(self):
        return self.instance.pk if self.instance else None

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
        if phone_exists(phone, exclude_pk=self._exclude_pk()):
            raise serializers.ValidationError(PHONE_TAKEN)
        return phone

    def validate_email(self, value):
        value = value.strip().lower()
        if value and email_exists(value, exclude_pk=self._exclude_pk()):
            raise serializers.ValidationError(EMAIL_TAKEN)
        return value

    def validate_username(self, value):
        value = value.strip()
        if value and admin_services.username_exists(
            value, exclude_pk=self._exclude_pk()
        ):
            raise serializers.ValidationError(admin_services.USERNAME_TAKEN)
        return value

    def _check_password(self, password, candidate):
        try:
            validate_password(password, user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc


class CreateUserSerializer(_UserWriteSerializer):
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True, max_length=254)

    def validate(self, attrs):
        if attrs["role"] in (User.Role.ADMIN, User.Role.MANAGER) and not attrs.get(
            "username"
        ):
            raise serializers.ValidationError(
                {"username": [_("A username is required for this role.")]}
            )
        self._check_password(
            attrs["password"],
            User(
                full_name=attrs["full_name"],
                phone=attrs["phone"],
                email=attrs.get("email", ""),
            ),
        )
        return attrs


class UpdateUserSerializer(_UserWriteSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    def validate_password(self, value):
        if not value:
            raise serializers.ValidationError(_("This field may not be blank."))
        return value

    def validate(self, attrs):
        role = attrs.get("role", self.instance.role)
        username = attrs.get("username", self.instance.username)
        if role in (User.Role.ADMIN, User.Role.MANAGER) and not username:
            raise serializers.ValidationError(
                {"username": [_("A username is required for this role.")]}
            )
        if "username" in attrs and not attrs["username"]:
            attrs["username"] = None
        if "password" in attrs:
            self._check_password(attrs["password"], self.instance)
        return attrs
