"""Driver performance (BL-062, BR-10). Months are calendar months in the server time zone."""

import re
from collections import defaultdict

from django.db.models import F, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from .models import Order, OrderRating, OrderStatusChange

MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def parse_month(value):
    if not value:
        return None
    if not MONTH.match(value):
        raise ValidationError({"month": [_("Use the format YYYY-MM.")]})
    return value


def _key(moment) -> str:
    return timezone.localtime(moment).strftime("%Y-%m")


def _delivered_at(order_ref):
    when = OrderStatusChange.objects.filter(
        order=OuterRef(order_ref), to_status=Order.Status.DELIVERED
    ).order_by("-id")
    return Subquery(when.values("created_at")[:1])


class _Bucket:
    __slots__ = ("cancelled", "delivered", "scores")

    def __init__(self):
        self.delivered = 0
        self.cancelled = 0
        self.scores = []

    def dump(self) -> dict:
        count = len(self.scores)
        average = round(sum(self.scores) / count, 1) if count else None
        return {
            "delivered": self.delivered,
            "cancelled": self.cancelled,
            "average_rating": average,
            "rating_count": count,
        }


def collect(driver_ids=None):
    """{driver_id: {month: bucket}} from three queries, so month boundaries are exact."""
    out = defaultdict(lambda: defaultdict(_Bucket))
    delivered = Order.objects.filter(
        status=Order.Status.DELIVERED, driver__isnull=False
    ).annotate(at=Coalesce(_delivered_at("pk"), F("modified_at")))
    cancelled = Order.objects.filter(
        status=Order.Status.CANCELLED, driver__isnull=False, cancelled_at__isnull=False
    )
    ratings = OrderRating.objects.annotate(
        at=Coalesce(_delivered_at("order_id"), F("order__modified_at"))
    )
    if driver_ids is not None:
        delivered = delivered.filter(driver_id__in=driver_ids)
        cancelled = cancelled.filter(driver_id__in=driver_ids)
        ratings = ratings.filter(driver_id__in=driver_ids)
    for driver_id, at in delivered.values_list("driver_id", "at"):
        out[driver_id][_key(at)].delivered += 1
    for driver_id, at in cancelled.values_list("driver_id", "cancelled_at"):
        out[driver_id][_key(at)].cancelled += 1
    for driver_id, at, score in ratings.values_list("driver_id", "at", "score"):
        out[driver_id][_key(at)].scores.append(score)
    return out


def summarise(months: dict, month=None) -> dict:
    """Metrics of one month, or of everything when ``month`` is None."""
    total = _Bucket()
    for key, bucket in months.items():
        if month is None or key == month:
            total.delivered += bucket.delivered
            total.cancelled += bucket.cancelled
            total.scores.extend(bucket.scores)
    return total.dump()


def driver_performance(driver_id, month=None) -> dict:
    months = collect([driver_id]).get(driver_id, {})
    return {
        "month": month,
        **summarise(months, month),
        "months": [
            {"month": key, **months[key].dump()} for key in sorted(months, reverse=True)
        ],
    }


def overview(drivers, month=None, ordering="delivered") -> list:
    data = collect([d.pk for d in drivers])
    rows = [
        {
            "id": d.pk,
            "full_name": d.full_name,
            "status": d.status,
            **summarise(data.get(d.pk, {}), month),
        }
        for d in drivers
    ]
    if ordering == "rating":
        # Best average first; drivers without ratings last; ties by name.
        rows.sort(
            key=lambda r: (
                r["average_rating"] is None,
                -(r["average_rating"] or 0),
                r["full_name"],
            )
        )
    else:
        rows.sort(key=lambda r: (-r["delivered"], r["full_name"]))
    return rows
