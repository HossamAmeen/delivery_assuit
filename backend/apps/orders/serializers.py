from rest_framework import serializers

from apps.users.models import User

from . import execute
from .assign import ACTIVE
from .models import Order, OrderItem, OrderRating, OrderStatusChange


def _place(order, prefix):
    return {
        "name": getattr(order, f"{prefix}_name"),
        "address": getattr(order, f"{prefix}_address"),
        "latitude": _num(getattr(order, f"{prefix}_latitude")),
        "longitude": _num(getattr(order, f"{prefix}_longitude")),
    }


def _num(value):
    return None if value is None else float(value)


class OrderItemSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        source="unit_price",
        max_digits=10,
        decimal_places=2,
        coerce_to_string=False,
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = ("name", "quantity", "price")


class OrderSerializer(serializers.ModelSerializer):
    """The order object of the contract. The client's phone is for Admin and Manager only."""

    client = serializers.SerializerMethodField()
    shop = serializers.SerializerMethodField()
    driver = serializers.SerializerMethodField()
    pickup = serializers.SerializerMethodField()
    delivery = serializers.SerializerMethodField()
    items = OrderItemSerializer(source="lines", many=True, read_only=True)
    delivery_fee = serializers.DecimalField(
        max_digits=8, decimal_places=2, coerce_to_string=False, read_only=True
    )
    assigned_at = serializers.DateTimeField(read_only=True, default=None)
    delivered_at = serializers.DateTimeField(read_only=True, default=None)
    next_action = serializers.SerializerMethodField()
    items_total = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "reference",
            "status",
            "client",
            "shop",
            "driver",
            "pickup",
            "delivery",
            "description",
            "items",
            "items_total",
            "delivery_fee",
            "assigned_at",
            "delivered_at",
            "next_action",
            "rating",
            "cancel_reason",
            "cancelled_at",
            "created_at",
            "modified_at",
        )

    def _user(self):
        return getattr(self.context.get("request"), "user", None)

    def _is_staff(self):
        user = self._user()
        return bool(user and user.role in (User.Role.ADMIN, User.Role.MANAGER))

    def _sees_contacts(self, obj) -> bool:
        """Contact numbers: staff always; the assigned driver only while the job is active (BR-16)."""
        user = self._user()
        if self._is_staff():
            return True
        return bool(
            user
            and user.role == User.Role.DRIVER
            and obj.driver_id == user.pk
            and obj.status in ACTIVE
        )

    def get_client(self, obj) -> dict:
        data = {"id": obj.client_id, "full_name": obj.client.full_name}
        if self._sees_contacts(obj):
            data["phone"] = obj.client.phone
        return data

    def get_shop(self, obj):
        if not obj.shop_id:
            return None
        data = {"id": obj.shop_id, "name": obj.shop.name}
        if self._sees_contacts(obj):
            data["phone"] = obj.shop.phone
        return data

    def get_driver(self, obj):
        # The driver's own phone is never sent to clients or traders (BR-16).
        if not obj.driver_id:
            return None
        return {"id": obj.driver_id, "full_name": obj.driver.full_name}

    def get_rating(self, obj):
        # Only the client who gave it and staff see a rating; the driver sees aggregates only.
        user = self._user()
        if not user:
            return None
        owner = user.role == User.Role.CLIENT and obj.client_id == user.pk
        if not (owner or self._is_staff()):
            return None
        rating = getattr(obj, "rating", None)
        if rating is None:
            return None
        return {
            "score": rating.score,
            "comment": rating.comment,
            "created_at": rating.created_at,
        }

    def get_items_total(self, obj):
        # Only priced lines count; None when no line has a price yet.
        priced = [l for l in obj.lines.all() if l.unit_price is not None]
        if not priced:
            return None
        return float(sum(l.unit_price * l.quantity for l in priced))

    def get_next_action(self, obj):
        user = self._user()
        if user and user.role == User.Role.DRIVER and obj.driver_id == user.pk:
            return execute.next_action(obj)
        return None

    def get_pickup(self, obj) -> dict:
        return _place(obj, "pickup")

    def get_delivery(self, obj) -> dict:
        return _place(obj, "delivery")


class ApproveSerializer(serializers.Serializer):
    delivery_fee = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=0,
        max_value=100000,
        required=False,
        allow_null=True,
    )


class RejectSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=3, max_length=500)


class AssignSerializer(serializers.Serializer):
    driver = serializers.IntegerField(min_value=1)


class DriverRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    phone = serializers.CharField()
    has_active_order = serializers.BooleanField()
    active_order_reference = serializers.CharField(allow_null=True)


class HistorySerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.full_name", read_only=True)

    class Meta:
        model = OrderStatusChange
        fields = ("from_status", "to_status", "actor_name", "reason", "created_at")


class OrderDetailSerializer(OrderSerializer):
    """The detail adds the status timeline (BL-027) for whoever can see the order."""

    history = HistorySerializer(many=True, read_only=True)

    class Meta(OrderSerializer.Meta):
        fields = (*OrderSerializer.Meta.fields, "history")


class FeeSerializer(serializers.Serializer):
    delivery_fee = serializers.DecimalField(
        max_digits=8, decimal_places=2, min_value=0, max_value=100000
    )


class CancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)


class RatingOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderRating
        fields = ("score", "comment", "created_at")
