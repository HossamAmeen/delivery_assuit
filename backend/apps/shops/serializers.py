from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.users.phone import is_valid_phone, normalize_phone

from . import services
from .models import Shop, ShopItem


class ShopSerializer(serializers.ModelSerializer):
    name = serializers.CharField(min_length=2, max_length=100)
    phone = serializers.CharField(max_length=32, allow_blank=True, required=False)
    description = serializers.CharField(
        max_length=500, allow_blank=True, required=False
    )
    can_accept_orders = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = (
            "id",
            "name",
            "phone",
            "description",
            "is_available",
            "can_accept_orders",
        )
        read_only_fields = ("id",)

    def get_can_accept_orders(self, obj) -> bool:
        return services.is_shop_orderable(obj)

    def validate_phone(self, value):
        value = value.strip()
        if not value:
            return ""
        if not is_valid_phone(value):
            raise serializers.ValidationError(
                _("Enter a valid phone number (8 to 15 digits).")
            )
        return normalize_phone(value)


class ShopItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(min_length=2, max_length=100)
    description = serializers.CharField(
        max_length=300, allow_blank=True, required=False
    )
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, coerce_to_string=False
    )

    class Meta:
        model = ShopItem
        fields = ("id", "name", "description", "is_hidden", "price", "created_at")
        read_only_fields = ("id", "price", "created_at")

    def validate_name(self, value):
        shop = self.context["shop"]
        pk = self.instance.pk if self.instance else None
        if services.name_taken(shop, value, exclude_pk=pk):
            raise serializers.ValidationError(services.NAME_TAKEN)
        return value


class PublicShopSerializer(serializers.ModelSerializer):
    """What a client sees in the shop list. No phone: contact numbers stay private (BR-16)."""

    class Meta:
        model = Shop
        fields = ("id", "name", "description")


class PublicItemSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, coerce_to_string=False
    )

    class Meta:
        model = ShopItem
        fields = ("id", "name", "description", "price")


class PublicShopDetailSerializer(PublicShopSerializer):
    items = serializers.SerializerMethodField()
    pickup_locations = serializers.SerializerMethodField()

    class Meta(PublicShopSerializer.Meta):
        fields = (*PublicShopSerializer.Meta.fields, "items", "pickup_locations")

    def get_items(self, obj) -> list:
        rows = ShopItem.objects.filter(shop=obj, is_hidden=False).order_by("id")
        return PublicItemSerializer(rows, many=True).data

    def get_pickup_locations(self, obj) -> list:
        return [
            {
                "id": loc.pk,
                "name": loc.name,
                "address": loc.address,
                "is_default": loc.is_default_pickup,
            }
            for loc in services.pickup_locations(obj)
        ]
