"""Throttles for password recovery (TASK-048): one bucket per IP, one per identifier."""

import hashlib

from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle

from .phone import looks_like_phone, normalize_phone


def identifier_key(identifier: str) -> str:
    """Stable form of an identifier, so "0100-123" and "0100123" share a bucket."""
    identifier = identifier.strip()
    if looks_like_phone(identifier):
        return normalize_phone(identifier)
    return identifier.lower()


class RecoveryIPThrottle(AnonRateThrottle):
    scope = "recovery"


class RecoveryIdentifierThrottle(SimpleRateThrottle):
    scope = "recovery_identifier"

    def get_cache_key(self, request, view):
        data = request.data if hasattr(request.data, "get") else {}
        identifier = data.get("identifier")
        if not isinstance(identifier, str) or not identifier.strip():
            return None
        digest = hashlib.sha256(identifier_key(identifier).encode()).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": digest}
