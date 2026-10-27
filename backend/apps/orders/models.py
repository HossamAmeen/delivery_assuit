from django.conf import settings
from django.db import models

from common.models import BaseModel


class Order(BaseModel):
    """A delivery order. Places are copied in, so later edits to a location never change it."""

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        AVAILABLE = "available", "Available"
        ASSIGNED = "assigned", "Assigned"
        PICKED_UP = "picked_up", "Picked up"
        IN_DELIVERY = "in_delivery", "In delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    # ORD-000012. Set right after the first insert, once the id is known.
    reference = models.CharField(max_length=20, unique=True, null=True, editable=False)
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    shop = models.ForeignKey(
        "shops.Shop",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="orders",
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="driver_orders",
    )
    pickup_name = models.CharField(max_length=100)
    pickup_address = models.CharField(max_length=500)
    pickup_latitude = models.DecimalField(
        max_digits=8, decimal_places=6, null=True, blank=True
    )
    pickup_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    delivery_name = models.CharField(max_length=100)
    delivery_address = models.CharField(max_length=500)
    delivery_latitude = models.DecimalField(
        max_digits=8, decimal_places=6, null=True, blank=True
    )
    delivery_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    description = models.TextField(blank=True)
    # Set by Admin or Manager only (BR-17), at review.
    delivery_fee = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CREATED, db_index=True
    )
    cancel_reason = models.CharField(max_length=500, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        ordering = ("-id",)

    def __str__(self) -> str:
        return self.reference or f"order-{self.pk}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.reference is None:
            self.reference = f"ORD-{self.pk:06d}"
            type(self).all_objects.filter(pk=self.pk).update(reference=self.reference)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(
        "shops.ShopItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    name = models.CharField(max_length=100)
    quantity = models.PositiveSmallIntegerField()
    # The item's price when the order was placed. Later price changes never touch it.
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta:
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.quantity} x {self.name}"


class OrderStatusChange(models.Model):
    """Who moved an order from one status to another, and when."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history")
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    reason = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.order_id}: {self.from_status} -> {self.to_status}"


class OrderFeeChange(models.Model):
    """Every set or change of an order's delivery fee (BR-17): old, new, who, when."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="fee_changes"
    )
    old_fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    new_fee = models.DecimalField(max_digits=8, decimal_places=2)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.order_id}: {self.old_fee} -> {self.new_fee}"


class OrderRating(models.Model):
    """The client's optional rating of the driver who delivered the order (BL-061)."""

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="rating")
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ratings"
    )
    score = models.PositiveSmallIntegerField()
    comment = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = (
            models.CheckConstraint(
                condition=models.Q(score__gte=1) & models.Q(score__lte=5),
                name="orders_rating_score_1_to_5",
            ),
        )

    def __str__(self) -> str:
        return f"{self.order_id}: {self.score}"
