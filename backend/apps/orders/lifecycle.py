"""The order lifecycle (BL-022). The only place that changes an order's status."""

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.audit import services as audit
from apps.notifications import services as notifications
from apps.users.models import User

from .models import Order, OrderStatusChange

S = Order.Status
STAFF, CLIENT, DRIVER = "staff", "client", "driver"

# (from, to) -> who may make the move.
TRANSITIONS = {
    (S.CREATED, S.AVAILABLE): (STAFF,),
    (S.CREATED, S.CANCELLED): (STAFF, CLIENT),
    # An edit sends an approved order back to review (BL-026); used by edit.py only.
    (S.AVAILABLE, S.CREATED): (STAFF, CLIENT),
    (S.AVAILABLE, S.ASSIGNED): (STAFF,),
    (S.AVAILABLE, S.CANCELLED): (STAFF, CLIENT),
    (S.ASSIGNED, S.PICKED_UP): (DRIVER,),
    (S.ASSIGNED, S.CANCELLED): (STAFF,),
    (S.PICKED_UP, S.IN_DELIVERY): (DRIVER,),
    (S.PICKED_UP, S.CANCELLED): (STAFF,),
    (S.IN_DELIVERY, S.DELIVERED): (DRIVER,),
    (S.IN_DELIVERY, S.CANCELLED): (STAFF,),
}
FINAL = (S.DELIVERED, S.CANCELLED)


def _roles_of(order, actor) -> set:
    roles = set()
    if actor.role in (User.Role.ADMIN, User.Role.MANAGER):
        roles.add(STAFF)
    if actor.role == User.Role.CLIENT and order.client_id == actor.pk:
        roles.add(CLIENT)
    if actor.role == User.Role.DRIVER and order.driver_id == actor.pk:
        roles.add(DRIVER)
    return roles


def _refuse(message):
    raise ValidationError({"status": [message]})


@transaction.atomic
def transition(order, to_status, actor, reason="", driver=None) -> Order:
    """Move ``order`` to ``to_status`` as ``actor``, or raise.

    Invalid moves are a 400 on ``status``. A valid move by the wrong person is a 403.
    ``driver`` is required for ``assigned`` and must be an active driver.
    """
    # Re-read under a lock so two concurrent moves cannot both pass the check.
    locked = Order.all_objects.select_for_update().get(pk=order.pk)
    current = locked.status
    if current in FINAL:
        _refuse(_("This order is final and cannot be changed."))
    allowed = TRANSITIONS.get((current, to_status))
    if allowed is None:
        _refuse(_("This status change is not allowed."))
    if not actor.is_operational or not (set(allowed) & _roles_of(locked, actor)):
        raise PermissionDenied(_("You cannot make this status change."))
    if to_status == S.ASSIGNED:
        if (
            driver is None
            or driver.role != User.Role.DRIVER
            or not driver.is_operational
        ):
            _refuse(_("Choose an active driver."))
        locked.driver = driver
    if to_status == S.CANCELLED:
        locked.cancel_reason = reason
        locked.cancelled_at = timezone.now()
        locked.cancelled_by = actor
    locked.status = to_status
    locked.save()
    OrderStatusChange.objects.create(
        order=locked,
        from_status=current,
        to_status=to_status,
        actor=actor,
        reason=reason,
    )
    audit.log(actor, "order.status", "order", locked.pk, f"{current} -> {to_status}")
    notifications.on_transition(locked, current, to_status, actor)
    order.refresh_from_db()
    return order


def record_creation(order, actor) -> None:
    """History row for the first status (no earlier status)."""
    OrderStatusChange.objects.create(
        order=order, from_status="", to_status=order.status, actor=actor
    )
    audit.log(actor, "order.status", "order", order.pk, f"-> {order.status}")
    if order.status == Order.Status.CREATED:
        notifications.on_order_created(order)
