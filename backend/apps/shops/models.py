from django.conf import settings
from django.db import models
from django.db.models.functions import Lower

from common.models import BaseModel


class Shop(BaseModel):
    """A trader's shop. One per trader, created on first use, unavailable until the trader opens it."""

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shop"
    )
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    description = models.CharField(max_length=500, blank=True)
    is_available = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name


class ShopItem(BaseModel):
    """A simple item in a shop's flat list. No price until Sprint 07 (BR-17)."""

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=300, blank=True)
    is_hidden = models.BooleanField(default=False)
    # Set by Admin or Manager only (Sprint 07). Never written from the trader API.
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    price_set_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-id",)
        constraints = (
            models.UniqueConstraint(
                Lower("name"),
                "shop",
                condition=models.Q(deleted_at__isnull=True),
                name="shops_item_name_ci_unique",
            ),
        )

    def __str__(self) -> str:
        return self.name
