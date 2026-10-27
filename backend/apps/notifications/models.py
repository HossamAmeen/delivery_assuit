from django.conf import settings
from django.db import models


class Notification(models.Model):
    """An in-app notification (BL-066). The frontend writes the sentence from ``kind``."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    kind = models.CharField(max_length=40)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    reference = models.CharField(max_length=20, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-id",)
        indexes = (models.Index(fields=("user", "read_at")),)

    def __str__(self) -> str:
        return f"{self.kind} -> user {self.user_id}"
