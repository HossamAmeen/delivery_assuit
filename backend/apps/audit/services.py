import logging

from django.db import transaction

from .models import AuditEntry

logger = logging.getLogger(__name__)


def log(actor, action, target_type, target_id, detail="") -> None:
    """Append one entry. Auditing must never break the action it records."""
    try:
        with transaction.atomic():
            AuditEntry.objects.create(
                actor=actor,
                action=action,
                target_type=target_type,
                target_id=target_id,
                detail=str(detail)[:255],
            )
    except Exception:
        logger.exception("Could not write an audit entry")
