"""Cancelling an order (BL-025, BL-055, BR-12). The lifecycle decides who may."""

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.users.models import User

from . import lifecycle
from .models import Order


def cancel(order, actor, reason="") -> Order:
    reason = (reason or "").strip()
    if actor.role in (User.Role.ADMIN, User.Role.MANAGER) and len(reason) < 3:
        # Staff cancellations are explained to the client.
        raise ValidationError({"reason": [_("Enter the reason for the cancellation.")]})
    return lifecycle.transition(order, Order.Status.CANCELLED, actor, reason=reason)
