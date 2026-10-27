"""Staff actions on other people's accounts (Admin and Manager, BR-14)."""

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from .exceptions import AdminProtected
from .models import AccountAction, User
from .permissions import can_manage_account
from .phone import normalize_phone
from .services import (
    EMAIL_TAKEN,
    PHONE_TAKEN,
    email_exists,
    phone_exists,
    revoke_refresh_family,
)

NOT_PENDING_APPROVE = _("Only a pending driver or trader can be approved.")
NOT_DEACTIVATED = _("Only a deactivated account can be activated.")
NOT_ACTIVE = _("Only an active account can be deactivated.")
USERNAME_TAKEN = _("A user with this username already exists.")
OWN_DELETE = _("You cannot delete your own account.")
OWN_ROLE = _("You cannot change your own role.")
OWN_DEACTIVATE = _("You cannot deactivate your own account.")
NOT_PENDING_REJECT = _("Only a pending driver or trader can be rejected.")
APPROVABLE_ROLES = (User.Role.DRIVER, User.Role.TRADER)


def ensure_can_manage(actor: User, target: User) -> None:
    """403 ``admin_protected`` when a Manager targets an Admin (BR-14)."""
    if not can_manage_account(actor, target):
        raise AdminProtected()


def is_publicly_operable(user: User) -> bool:
    """True when a driver or trader may be assigned orders or shown to clients.

    Pending and rejected accounts are not (BR-5, BR-15). Later sprints (orders,
    shops) MUST call this before assigning a driver or listing a trader.
    """
    return user.is_operational


def _lock(target: User) -> User:
    return User.objects.select_for_update().get(pk=target.pk)


def _record(target: User, actor: User, action: str, reason: str = "") -> None:
    AccountAction.objects.create(user=target, actor=actor, action=action, reason=reason)
    from apps.audit import services as audit

    audit.log(actor, f"account.{action}", "user", target.pk, reason)


def approve_account(target: User, actor: User) -> User:
    """pending_approval -> active for a driver or trader."""
    ensure_can_manage(actor, target)
    with transaction.atomic():
        target = _lock(target)
        if (
            target.status != User.Status.PENDING_APPROVAL
            or target.role not in APPROVABLE_ROLES
        ):
            raise ValidationError({"status": [NOT_PENDING_APPROVE]})
        target.status = User.Status.ACTIVE
        target.rejection_reason = ""
        target.save(update_fields=["status", "rejection_reason", "modified_at"])
        _record(target, actor, AccountAction.Action.APPROVED)
    return target


def reject_account(target: User, actor: User, reason: str = "") -> User:
    """pending_approval -> rejected for a driver or trader, with an optional reason."""
    ensure_can_manage(actor, target)
    with transaction.atomic():
        target = _lock(target)
        if (
            target.status != User.Status.PENDING_APPROVAL
            or target.role not in APPROVABLE_ROLES
        ):
            raise ValidationError({"status": [NOT_PENDING_REJECT]})
        target.status = User.Status.REJECTED
        target.rejection_reason = reason
        target.save(update_fields=["status", "rejection_reason", "modified_at"])
        _record(target, actor, AccountAction.Action.REJECTED, reason)
    return target


def activate_account(target: User, actor: User) -> User:
    """deactivated -> active. Old refresh tokens are not restored."""
    ensure_can_manage(actor, target)
    with transaction.atomic():
        target = _lock(target)
        if target.status != User.Status.DEACTIVATED:
            raise ValidationError({"status": [NOT_DEACTIVATED]})
        target.status = User.Status.ACTIVE
        target.save(update_fields=["status", "modified_at"])
        _record(target, actor, AccountAction.Action.ACTIVATED)
    return target


def deactivate_account(target: User, actor: User) -> User:
    """active -> deactivated, and kill every refresh token of the target.

    The current access token keeps working until it expires, but the status check
    on every request already answers 403 ``account_deactivated``.

    Orders do not exist yet. When they do (Sprint 05+), deactivating a driver MUST
    leave the orders assigned to that driver in place: this function only changes
    the account status and revokes tokens.
    """
    ensure_can_manage(actor, target)
    if target.pk == actor.pk:
        raise ValidationError({"non_field_errors": [OWN_DEACTIVATE]})
    with transaction.atomic():
        target = _lock(target)
        if target.status != User.Status.ACTIVE:
            raise ValidationError({"status": [NOT_ACTIVE]})
        target.status = User.Status.DEACTIVATED
        target.save(update_fields=["status", "modified_at"])
        revoke_refresh_family(target.pk)
        _record(target, actor, AccountAction.Action.DEACTIVATED)
    return target


# --- Create, edit, delete (TASK-052) --------------------------------------------


def username_exists(username: str, *, exclude_pk: int | None = None) -> bool:
    return User.all_objects.filter(username=username).exclude(pk=exclude_pk).exists()


def _staff_flags(role: str) -> dict:
    """Only an Admin is Django staff and superuser (matches ``create_admin``)."""
    is_admin = role == User.Role.ADMIN
    return {"is_staff": is_admin, "is_superuser": is_admin}


def _taken(exc_fields: dict) -> ValidationError:
    messages = {"phone": PHONE_TAKEN, "email": EMAIL_TAKEN, "username": USERNAME_TAKEN}
    for field, value in exc_fields.items():
        if value and _exists(field, value):
            return ValidationError({field: [messages[field]]})
    return ValidationError({"phone": [PHONE_TAKEN]})


def _exists(field: str, value: str) -> bool:
    if field == "phone":
        return phone_exists(value)
    if field == "email":
        return email_exists(value)
    return username_exists(value)


def ensure_can_assign_role(actor: User, role: str) -> None:
    """Only an Admin may create or promote an Admin (BR-14)."""
    if role == User.Role.ADMIN and actor.role != User.Role.ADMIN:
        raise AdminProtected()


def create_user(actor: User, *, password: str, **fields) -> User:
    """Create an ``active`` account. Role-based permission was checked by the caller."""
    role = fields["role"]
    ensure_can_assign_role(actor, role)
    try:
        with transaction.atomic():
            user = User(
                username=fields.get("username") or None,
                phone=normalize_phone(fields["phone"]) or None,
                email=fields.get("email", ""),
                full_name=fields["full_name"],
                role=role,
                status=User.Status.ACTIVE,
                **_staff_flags(role),
            )
            user.set_password(password)
            user.save()
    except IntegrityError:
        raise _taken(
            {
                "phone": fields["phone"],
                "email": fields.get("email", ""),
                "username": fields.get("username", ""),
            }
        ) from None
    return user


def update_user(actor: User, target: User, *, password: str | None = None, **changes):
    """Edit another account's details; a new password revokes its refresh tokens."""
    ensure_can_manage(actor, target)
    if "role" in changes:
        ensure_can_assign_role(actor, changes["role"])
        if changes["role"] != target.role and target.pk == actor.pk:
            raise ValidationError({"role": [OWN_ROLE]})
    try:
        with transaction.atomic():
            target = _lock(target)
            fields = []
            for name, value in changes.items():
                setattr(target, name, value)
                fields.append(name)
            if "role" in changes:
                for name, value in _staff_flags(changes["role"]).items():
                    setattr(target, name, value)
                    fields.append(name)
            if password is not None:
                target.set_password(password)
                fields.append("password")
            if fields:
                target.save(update_fields=[*fields, "modified_at"])
            if password is not None:
                revoke_refresh_family(target.pk)
    except IntegrityError:
        raise _taken(
            {k: changes.get(k, "") for k in ("phone", "email", "username")}
        ) from None
    return target


def delete_user(actor: User, target: User) -> None:
    """Soft-delete. The user can no longer log in and their tokens die."""
    ensure_can_manage(actor, target)
    if target.pk == actor.pk:
        raise ValidationError({"non_field_errors": [OWN_DELETE]})
    with transaction.atomic():
        target = _lock(target)
        target.deleted_at = timezone.now()
        target.save(update_fields=["deleted_at", "modified_at"])
        revoke_refresh_family(target.pk)
