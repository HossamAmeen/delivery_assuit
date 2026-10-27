"""Who sees which orders (BL-024). Every order read goes through ``visible_orders``."""

from django.db.models import Exists, OuterRef, Subquery

from apps.users.models import User

from .models import Order, OrderStatusChange


def visible_orders(user):
    """Orders ``user`` may see; anything else must behave as if it does not exist."""
    when = OrderStatusChange.objects.filter(order=OuterRef("pk")).order_by("-id")
    qs = (
        Order.objects.select_related("client", "shop", "driver", "rating")
        .prefetch_related("lines", "history__actor")
        .annotate(
            assigned_at=Subquery(
                when.filter(to_status=Order.Status.ASSIGNED).values("created_at")[:1]
            ),
            delivered_at=Subquery(
                when.filter(to_status=Order.Status.DELIVERED).values("created_at")[:1]
            ),
        )
    )
    role = user.role
    if role in (User.Role.ADMIN, User.Role.MANAGER):
        return qs
    if role == User.Role.CLIENT:
        return qs.filter(client=user)
    if role == User.Role.DRIVER:
        return qs.filter(driver=user)
    if role == User.Role.TRADER:
        # Only after Admin/Manager approval (BR-11): an order rejected at review never shows.
        approved = OrderStatusChange.objects.filter(
            order=OuterRef("pk"), to_status=Order.Status.AVAILABLE
        )
        return qs.filter(shop__owner=user).filter(Exists(approved))
    return qs.none()
