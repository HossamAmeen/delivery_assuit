"""Creating an order from a client's request (BL-047 shop order, BL-048 direct delivery)."""

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.locations.models import SavedAddress
from apps.locations.serializers import COORDINATE_FIELDS
from apps.shops import services as shop_services
from apps.shops.models import ShopItem

from . import lifecycle
from .models import Order, OrderItem

MAX_LINES = 50
REQUIRED = _("This field is required.")


class PlaceInput(serializers.Serializer):
    """A place typed into the form (same rules as a location or saved address)."""

    name = serializers.CharField(min_length=2, max_length=100)
    address = serializers.CharField(min_length=3, max_length=500)
    latitude = serializers.DecimalField(
        **COORDINATE_FIELDS["latitude"],
        coerce_to_string=False,
        required=False,
        allow_null=True,
    )
    longitude = serializers.DecimalField(
        **COORDINATE_FIELDS["longitude"],
        coerce_to_string=False,
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        lat, lng = attrs.get("latitude"), attrs.get("longitude")
        if lat is None and lng is not None:
            raise serializers.ValidationError(
                {"latitude": [_("Latitude is required with longitude.")]}
            )
        if lng is None and lat is not None:
            raise serializers.ValidationError(
                {"longitude": [_("Longitude is required with latitude.")]}
            )
        return attrs


class LineInput(serializers.Serializer):
    item = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=99)


class OrderCreateSerializer(serializers.Serializer):
    shop = serializers.IntegerField(required=False, min_value=1)
    pickup_location = serializers.IntegerField(required=False, min_value=1)
    items = LineInput(many=True, required=False, allow_empty=True)
    description = serializers.CharField(
        required=False, allow_blank=True, max_length=1000
    )
    pickup = PlaceInput(required=False)
    pickup_saved_address = serializers.IntegerField(required=False, min_value=1)
    delivery = PlaceInput(required=False)
    delivery_saved_address = serializers.IntegerField(required=False, min_value=1)

    def _place(self, attrs, key, errors):
        """The place for ``key`` from either the typed object or an own saved address."""
        typed = attrs.get(key)
        saved_id = attrs.get(f"{key}_saved_address")
        if typed is not None and saved_id is not None:
            errors[key] = [_("Send the place or a saved address, not both.")]
        elif saved_id is not None:
            address = SavedAddress.objects.filter(
                owner=self.context["client"], pk=saved_id
            ).first()
            if address is None:
                # Same message for "not yours" and "does not exist".
                errors[f"{key}_saved_address"] = [_("Saved address not found.")]
                return None
            return {
                "name": address.name,
                "address": address.address,
                "latitude": address.latitude,
                "longitude": address.longitude,
            }
        elif typed is not None:
            return {
                "name": typed["name"],
                "address": typed["address"],
                "latitude": typed.get("latitude"),
                "longitude": typed.get("longitude"),
            }
        else:
            errors[key] = [REQUIRED]
        return None

    def validate(self, attrs):
        sent = set(self.initial_data)
        errors = {}
        is_shop_order = "shop" in sent
        not_accepted = _("This field is not accepted for this kind of order.")

        if is_shop_order:
            for key in ("pickup", "pickup_saved_address"):
                if key in sent:
                    errors[key] = [not_accepted]
            shop = shop_services.orderable_shops().filter(pk=attrs["shop"]).first()
            if shop is None:
                errors["shop"] = [_("This shop is not available for orders.")]
            pickup_place = self._shop_pickup(shop, attrs, errors)
            lines = self._lines(shop, attrs, errors)
        else:
            for key in ("pickup_location", "items"):
                if key in sent:
                    errors[key] = [not_accepted]
            shop, lines = None, []
            pickup_place = self._place(attrs, "pickup", errors)
            if len(attrs.get("description", "").strip()) < 3:
                errors["description"] = [
                    _("Describe what is being delivered (at least 3 characters).")
                ]
        delivery_place = self._place(attrs, "delivery", errors)
        if errors:
            raise serializers.ValidationError(errors)
        return {
            "shop": shop,
            "pickup": pickup_place,
            "delivery": delivery_place,
            "lines": lines,
            "description": attrs.get("description", "").strip(),
        }

    def _shop_pickup(self, shop, attrs, errors):
        if shop is None:
            return None
        locations = list(shop_services.pickup_locations(shop))
        chosen_id = attrs.get("pickup_location")
        if chosen_id is None:
            chosen = locations[0]  # default first
        else:
            chosen = next((loc for loc in locations if loc.pk == chosen_id), None)
            if chosen is None:
                errors["pickup_location"] = [
                    _("Choose one of the shop's pickup locations.")
                ]
                return None
        return {
            "name": chosen.name,
            "address": chosen.address,
            "latitude": chosen.latitude,
            "longitude": chosen.longitude,
        }

    def _lines(self, shop, attrs, errors):
        raw = attrs.get("items") or []
        if not raw:
            errors["items"] = [_("Choose at least one item.")]
            return []
        if len(raw) > MAX_LINES:
            errors["items"] = [
                _("You can order at most %(n)d different items.") % {"n": MAX_LINES}
            ]
            return []
        ids = [line["item"] for line in raw]
        if len(set(ids)) != len(ids):
            errors["items"] = [_("Each item can appear only once.")]
            return []
        if shop is None:
            return []
        found = {
            i.pk: i
            for i in ShopItem.objects.filter(shop=shop, is_hidden=False, pk__in=ids)
        }
        if len(found) != len(ids):
            errors["items"] = [_("One or more items are not available from this shop.")]
            return []
        return [(found[line["item"]], line["quantity"]) for line in raw]


@transaction.atomic
def create_order(client, data) -> Order:
    pickup, delivery = data["pickup"], data["delivery"]
    order = Order.objects.create(
        client=client,
        shop=data["shop"],
        pickup_name=pickup["name"],
        pickup_address=pickup["address"],
        pickup_latitude=pickup["latitude"],
        pickup_longitude=pickup["longitude"],
        delivery_name=delivery["name"],
        delivery_address=delivery["address"],
        delivery_latitude=delivery["latitude"],
        delivery_longitude=delivery["longitude"],
        description=data["description"],
    )
    OrderItem.objects.bulk_create(
        OrderItem(
            order=order,
            item=item,
            name=item.name,
            quantity=qty,
            unit_price=item.price,
        )
        for item, qty in data["lines"]
    )
    lifecycle.record_creation(order, client)
    return order
