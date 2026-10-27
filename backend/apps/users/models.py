from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models.functions import Lower

from common.managers import AllManager, DeletedManager
from common.models import BaseModel

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """Minimal custom user. Login identifier is the username or the phone number."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Manager"
        DRIVER = "driver", "Driver"
        TRADER = "trader", "Trader"
        CLIENT = "client", "Client"

    class Status(models.TextChoices):
        PENDING_APPROVAL = "pending_approval", "Pending approval"
        ACTIVE = "active", "Active"
        DEACTIVATED = "deactivated", "Deactivated"
        REJECTED = "rejected", "Rejected"

    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(blank=True)
    full_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    rejection_reason = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()
    deleted_objects = DeletedManager()
    all_objects = AllManager()

    USERNAME_FIELD = "username"

    class Meta:
        ordering = ("id",)
        constraints = (
            # Case-insensitive unique email for live accounts. Empty emails repeat.
            models.UniqueConstraint(
                Lower("email"),
                name="users_user_email_ci_unique",
                condition=~models.Q(email="") & models.Q(deleted_at__isnull=True),
            ),
        )

    def __str__(self) -> str:
        return self.username or self.phone or f"user-{self.pk}"

    @property
    def is_operational(self) -> bool:
        """True when the account may use the API: status active and not deleted."""
        return self.status == self.Status.ACTIVE and self.deleted_at is None


class PasswordResetToken(models.Model):
    """A single-use password reset link. Only the hash of the token is stored."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="password_reset_tokens"
    )
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"reset-token user={self.user_id}"


class AccountAction(models.Model):
    """Who approved, rejected, activated or deactivated an account, and when."""

    class Action(models.TextChoices):
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        ACTIVATED = "activated", "Activated"
        DEACTIVATED = "deactivated", "Deactivated"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="account_actions"
    )
    actor = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-id",)

    def __str__(self) -> str:
        return f"{self.action} user={self.user_id} by={self.actor_id}"
