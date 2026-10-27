from django.contrib.auth.models import BaseUserManager

from apps.users.phone import normalize_phone
from common.managers import SoftDeleteQuerySet


class UserManager(BaseUserManager.from_queryset(SoftDeleteQuerySet)):
    """Default user manager: hides soft-deleted users (use ``all_objects`` for all)."""

    use_in_migrations = False

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError("The username must be set.")
        return self._build_user(username, password, **extra_fields)

    def _build_user(self, username, password, **extra_fields):
        if username:
            username = self.model.normalize_username(username)
        else:
            username = None  # NULL, so the unique constraint ignores it
        # Empty phone/email are stored as NULL / "" so uniqueness works for blanks.
        extra_fields["phone"] = normalize_phone(extra_fields.get("phone")) or None
        if extra_fields.get("email"):
            extra_fields["email"] = self.normalize_email(extra_fields["email"])
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, password, **extra_fields)

    def create_account(self, phone, password, **extra_fields):
        """Create a user identified by phone only (no username), e.g. self-registration.

        ``role`` and ``status`` must come from trusted server code, never a request.
        """
        if not normalize_phone(phone):
            raise ValueError("The phone must be set.")
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._build_user(None, password, phone=phone, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        from apps.users.models import User

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        if extra_fields["is_staff"] is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields["is_superuser"] is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(username, password, **extra_fields)
