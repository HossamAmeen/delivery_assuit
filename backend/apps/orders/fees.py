"""Delivery fee changes (BL-077, BR-17). Every change is recorded."""

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.audit import services as audit

from .lifecycle import FINAL
from .models import Order, OrderFeeChange


def record(order, actor, fee) -> None:
    OrderFeeChange.objects.create(
        order=order, old_fee=order.delivery_fee, new_fee=fee, actor=actor
    )
    audit.log(actor, "order.fee", "order", order.pk, f"{order.delivery_fee} -> {fee}")


@transaction.atomic
def set_fee(order, actor, fee) -> Order:
    locked = Order.all_objects.select_for_update().get(pk=order.pk)
    if locked.status in FINAL:
        raise ValidationError(
            {"status": [_("The fee of a finished order cannot be changed.")]}
        )
    record(locked, actor, fee)
    locked.delivery_fee = fee
    locked.save(update_fields=["delivery_fee", "modified_at"])
    order.refresh_from_db()
    return order
