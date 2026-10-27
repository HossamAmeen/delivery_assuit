from django.conf import settings
from django.db import models


class AppendOnlyQuerySet(models.QuerySet):
    """The audit log is never edited or removed through the application (BL-069)."""

    def update(self, **kwargs):
        raise PermissionError("The audit log is append-only.")

    def delete(self):
        raise PermissionError("The audit log is append-only.")


class AuditEntry(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    action = models.CharField(max_length=40, db_index=True)
    target_type = models.CharField(max_length=20)
    target_id = models.PositiveBigIntegerField()
    detail = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        ordering = ("-id",)
        indexes = (models.Index(fields=("target_type", "target_id")),)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError("The audit log is append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("The audit log is append-only.")

    def __str__(self) -> str:
        return f"{self.action} {self.target_type}:{self.target_id}"
