"""Assigning an available order to a driver (BL-031, BR-1, BR-3, BR-4)."""

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.users.models import User

from . import lifecycle
from .models import Order

ACTIVE = (Order.Status.ASSIGNED, Order.Status.PICKED_UP, Order.Status.IN_DELIVERY)


def has_active_order(driver) -> bool:
    return Order.objects.filter(driver=driver, status__in=ACTIVE).exists()


@transaction.atomic
def assign(order, actor, driver_id) -> Order:
    # Always lock the order first, then the driver, so concurrent calls cannot deadlock.
    locked = Order.all_objects.select_for_update().get(pk=order.pk)
    if locked.status != Order.Status.AVAILABLE:
        raise ValidationError(
            {"status": [_("Only an available order can be assigned.")]}
        )
    driver = (
        User.objects.select_for_update()
        .filter(pk=driver_id, role=User.Role.DRIVER, status=User.Status.ACTIVE)
        .first()
    )
    if driver is None:
        raise ValidationError({"driver": [_("Choose an active driver.")]})
    if has_active_order(driver):
        raise ValidationError(
            {"driver": [_("This driver already has an active order.")]}
        )
    return lifecycle.transition(order, Order.Status.ASSIGNED, actor, driver=driver)
