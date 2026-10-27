"""Staff-only price setting for shop items (BL-077, BR-17)."""

from django.utils import timezone
from rest_framework import serializers

from apps.audit import services as audit


class PriceSerializer(serializers.Serializer):
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        max_value=100000,
        allow_null=True,
        coerce_to_string=False,
    )


def set_price(item, actor, price):
    audit.log(actor, "item.price", "item", item.pk, f"{item.price} -> {price}")
    item.price = price
    item.price_set_by = actor
    item.price_set_at = timezone.now()
    item.save(update_fields=["price", "price_set_by", "price_set_at", "modified_at"])
    return item
