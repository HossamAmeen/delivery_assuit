from django.conf import settings
from django.db import models

from common.models import BaseModel


class PlaceFields(BaseModel):
    """A named place: name, address text, optional coordinates (BL-019)."""

    name = models.CharField(max_length=100)
    address = models.CharField(max_length=500)
    latitude = models.DecimalField(
        max_digits=8, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    class Meta:
        abstract = True


class Location(PlaceFields):
    """A trader's branch. Soft deleted, so past orders keep their own copy of the place."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="locations"
    )
    is_pickup = models.BooleanField(default=True)
    is_delivery = models.BooleanField(default=False)
    is_default_pickup = models.BooleanField(default=False)

    class Meta:
        ordering = ("-id",)
        constraints = (
            models.UniqueConstraint(
                fields=("owner",),
                condition=models.Q(is_default_pickup=True)
                & models.Q(deleted_at__isnull=True),
                name="locations_one_default_pickup_per_owner",
            ),
        )

    def __str__(self) -> str:
        return f"{self.name} (owner {self.owner_id})"


class SavedAddress(PlaceFields):
    """A client's saved address (BL-076)."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_addresses",
    )

    class Meta:
        ordering = ("-id",)

    def __str__(self) -> str:
        return f"{self.name} (owner {self.owner_id})"
