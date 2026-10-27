from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def soft_delete(self):
        return self.update(deleted_at=timezone.now(), modified_at=timezone.now())

    def restore(self):
        return self.update(deleted_at=None, modified_at=timezone.now())


class ActiveManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """Default manager: only records that are not soft-deleted."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class DeletedManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """Only soft-deleted records."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=False)


class AllManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """Every record, deleted or not."""
