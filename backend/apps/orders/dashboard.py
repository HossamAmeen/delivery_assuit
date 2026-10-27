"""Staff dashboard counts (BL-053). Accounts are not filtered; orders are, by creation time."""

import datetime

from django.db.models import Count, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.users.models import User

from .models import Order

PERIODS = ("today", "week", "month", "custom")


def _date(value, field):
    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValidationError(
            {field: [_("Enter a valid date (YYYY-MM-DD).")]}
        ) from None


def date_range(period, date_from=None, date_to=None):
    """(start, end) dates inclusive, or None for all-time."""
    if not period:
        return None
    if period not in PERIODS:
        raise ValidationError({"period": [_("Choose today, week, month or custom.")]})
    today = timezone.localdate()
    if period == "today":
        return today, today
    if period == "week":
        return today - datetime.timedelta(days=6), today
    if period == "month":
        return today.replace(day=1), today
    start, end = _date(date_from, "from"), _date(date_to, "to")
    if start > end:
        raise ValidationError(
            {"from": [_("The start date must not be after the end date.")]}
        )
    return start, end


def _accounts(role):
    S = User.Status
    counts = User.objects.filter(role=role).aggregate(
        total=Count("pk"),
        active=Count("pk", filter=Q(status=S.ACTIVE)),
        inactive=Count("pk", filter=Q(status=S.DEACTIVATED)),
        pending=Count("pk", filter=Q(status=S.PENDING_APPROVAL)),
        rejected=Count("pk", filter=Q(status=S.REJECTED)),
    )
    return counts


def build(period=None, date_from=None, date_to=None) -> dict:
    window = date_range(period, date_from, date_to)
    orders = Order.objects.all()
    if window:
        orders = orders.filter(
            created_at__date__gte=window[0], created_at__date__lte=window[1]
        )
    S = Order.Status
    order_counts = orders.aggregate(
        total=Count("pk"),
        pending=Count("pk", filter=Q(status__in=(S.CREATED, S.AVAILABLE))),
        in_progress=Count(
            "pk", filter=Q(status__in=(S.ASSIGNED, S.PICKED_UP, S.IN_DELIVERY))
        ),
        delivered=Count("pk", filter=Q(status=S.DELIVERED)),
        cancelled=Count("pk", filter=Q(status=S.CANCELLED)),
    )
    return {
        "period": period or "all",
        "drivers": _accounts(User.Role.DRIVER),
        "traders": _accounts(User.Role.TRADER),
        "clients": {"total": User.objects.filter(role=User.Role.CLIENT).count()},
        "orders": order_counts,
    }
