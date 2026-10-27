"""Who is told about what (BL-066). Notifying never blocks the action that caused it."""

import logging

from django.db import transaction

from apps.users.models import User

from .models import Notification

logger = logging.getLogger(__name__)

STATUS_KIND = {
    "picked_up": "order_picked_up",
    "in_delivery": "order_in_delivery",
    "delivered": "order_delivered",
}


def _staff():
    return User.objects.filter(
        role__in=(User.Role.ADMIN, User.Role.MANAGER), status=User.Status.ACTIVE
    )


def _send(users, kind, order=None):
    seen, rows = set(), []
    for user in users:
        if user is None or user.pk in seen:
            continue
        seen.add(user.pk)
        rows.append(
            Notification(
                user=user,
                kind=kind,
                order=order,
                reference=order.reference if order else "",
            )
        )
    Notification.objects.bulk_create(rows)


def _safe(fn, *args):
    try:
        with transaction.atomic():
            fn(*args)
    except Exception:
        logger.exception("Could not write notifications")


def on_order_created(order) -> None:
    _safe(lambda: _send(_staff(), "order_waiting_review", order))


def on_transition(order, from_status, to_status, actor) -> None:
    _safe(_transition, order, from_status, to_status, actor)


def _transition(order, frm, to, actor):
    client, driver = order.client, order.driver
    by_client = actor is not None and actor.pk == order.client_id
    if frm == "available" and to == "created":
        _send(_staff(), "order_waiting_review", order)
    elif frm == "created" and to == "available":
        _send([client], "order_approved", order)
    elif frm == "created" and to == "cancelled":
        # A staff cancel of a new order is the review rejection; the client's own cancel tells no one.
        if not by_client:
            _send([client], "order_rejected", order)
    elif to == "assigned":
        _send([driver, client], "order_assigned", order)
    elif to in STATUS_KIND:
        _send([client], STATUS_KIND[to], order)
    elif to == "cancelled":
        recipients = [] if by_client else [client]
        if driver is not None and (actor is None or actor.pk != driver.pk):
            recipients.append(driver)
        _send(recipients, "order_cancelled", order)


def on_account_registered(user) -> None:
    if user.role in (User.Role.DRIVER, User.Role.TRADER):
        _safe(lambda: _send(_staff(), "account_waiting_approval"))
