"""Admin/Manager review of a new order (BL-023, BR-11, BR-17)."""

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from . import fees, lifecycle
from .models import Order


@transaction.atomic
def approve(order, actor, delivery_fee=None) -> Order:
    # The transition checks status and role first; the fee is only stored if it succeeds.
    lifecycle.transition(order, Order.Status.AVAILABLE, actor)
    if delivery_fee is not None:
        fees.record(order, actor, delivery_fee)
        order.delivery_fee = delivery_fee
        order.save(update_fields=["delivery_fee", "modified_at"])
    return order


@transaction.atomic
def reject(order, actor, reason) -> Order:
    # Review applies to new orders only. Cancelling an order that is already available
    # is a different action (BL-025), so it must not pass through here.
    locked = Order.all_objects.select_for_update().get(pk=order.pk)
    if locked.status != Order.Status.CREATED:
        raise ValidationError({"status": [_("Only a new order can be reviewed.")]})
    return lifecycle.transition(order, Order.Status.CANCELLED, actor, reason=reason)
