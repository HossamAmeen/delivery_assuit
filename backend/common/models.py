from django.db import models
from django.utils import timezone

from .managers import ActiveManager, AllManager, DeletedManager


class BaseModel(models.Model):
    """Abstract base: timestamps plus soft delete.

    Concrete models inherit the three managers; ``objects`` returns only
    active (not soft-deleted) rows.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = ActiveManager()
    deleted_objects = DeletedManager()
    all_objects = AllManager()

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "modified_at"])

    def restore(self) -> None:
        self.deleted_at = None
        self.save(update_fields=["deleted_at", "modified_at"])
