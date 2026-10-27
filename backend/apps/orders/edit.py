"""Editing an order before a driver is assigned (BL-026, BR-13)."""

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.users.models import User

from . import lifecycle
from .create import LineInput, OrderCreateSerializer, PlaceInput
from .models import Order, OrderItem

S = Order.Status
EDITABLE = (S.CREATED, S.AVAILABLE)
NOT_ACCEPTED = _("This field is not accepted for this kind of order.")


class OrderEditSerializer(OrderCreateSerializer):
    """Same fields and rules as creation, all optional; only what is sent is validated."""

    # Redeclared so nothing is required on edit.
    items = LineInput(many=True, required=False, allow_empty=True)
    pickup = PlaceInput(required=False)
    delivery = PlaceInput(required=False)

    def validate(self, attrs):
        order = self.context["order"]
        sent = set(self.initial_data)
        errors = {}
        shop = order.shop
        out = {}

        if "shop" in sent:
            errors["shop"] = [_("The shop of an order cannot be changed.")]
        if shop is not None:
            for key in ("pickup", "pickup_saved_address"):
                if key in sent:
                    errors[key] = [NOT_ACCEPTED]
            if "pickup_location" in sent:
                place = self._shop_pickup(shop, attrs, errors)
                if place:
                    out["pickup"] = place
            if "items" in sent:
                lines = self._lines(shop, attrs, errors)
                if lines:
                    out["lines"] = lines
        else:
            for key in ("pickup_location", "items"):
                if key in sent:
                    errors[key] = [NOT_ACCEPTED]
            if sent & {"pickup", "pickup_saved_address"}:
                place = self._place(attrs, "pickup", errors)
                if place:
                    out["pickup"] = place
        if sent & {"delivery", "delivery_saved_address"}:
            place = self._place(attrs, "delivery", errors)
            if place:
                out["delivery"] = place
        if "description" in sent:
            text = attrs.get("description", "").strip()
            if shop is None and len(text) < 3:
                errors["description"] = [
                    _("Describe what is being delivered (at least 3 characters).")
                ]
            out["description"] = text
        if errors:
            raise serializers.ValidationError(errors)
        return out


def _check_allowed(order, actor):
    is_staff = actor.role in (User.Role.ADMIN, User.Role.MANAGER)
    is_owner = actor.role == User.Role.CLIENT and order.client_id == actor.pk
    if not (is_staff or is_owner):
        raise PermissionDenied(_("You cannot edit this order."))
    if order.status not in EDITABLE:
        if is_owner:
            # BR-13: after assignment the client may not edit.
            raise PermissionDenied(_("This order can no longer be edited."))
        raise ValidationError({"status": [_("This order can no longer be edited.")]})


@transaction.atomic
def edit_order(order, actor, changes) -> Order:
    locked = Order.all_objects.select_for_update().get(pk=order.pk)
    _check_allowed(locked, actor)
    for side in ("pickup", "delivery"):
        place = changes.get(side)
        if place:
            for field in ("name", "address", "latitude", "longitude"):
                setattr(locked, f"{side}_{field}", place[field])
    if "description" in changes:
        locked.description = changes["description"]
    locked.save()
    if "lines" in changes:
        locked.lines.all().delete()
        OrderItem.objects.bulk_create(
            OrderItem(
                order=locked,
                item=item,
                name=item.name,
                quantity=qty,
                unit_price=item.price,
            )
            for item, qty in changes["lines"]
        )
    if locked.status == S.AVAILABLE:
        # The simpler BL-026 option: an approved order goes back to review.
        lifecycle.transition(locked, S.CREATED, actor, reason="edited")
    order.refresh_from_db()
    return order
