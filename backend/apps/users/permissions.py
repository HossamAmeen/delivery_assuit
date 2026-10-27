from rest_framework.permissions import BasePermission

from .models import User

Role = User.Role


class IsOperational(BasePermission):
    """Authenticated and the account status is ``active`` (and not deleted)."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_operational)


class _HasRole(BasePermission):
    roles: tuple = ()

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_operational
            and user.role in self.roles
        )


class IsAdmin(_HasRole):
    roles = (Role.ADMIN,)


class IsAdminOrManager(_HasRole):
    roles = (Role.ADMIN, Role.MANAGER)


class IsDriver(_HasRole):
    roles = (Role.DRIVER,)


class IsTrader(_HasRole):
    roles = (Role.TRADER,)


class IsClient(_HasRole):
    roles = (Role.CLIENT,)


def can_manage_account(actor, target) -> bool:
    """Policy: Admin manages anyone; Manager manages everyone except Admins (BR-14)."""
    if actor is None or not getattr(actor, "is_authenticated", False):
        return False
    if not actor.is_operational:
        return False
    if actor.role == Role.ADMIN:
        return True
    if actor.role == Role.MANAGER:
        return target.role != Role.ADMIN
    return False
