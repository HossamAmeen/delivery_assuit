"""Startup checks that refuse placeholder or weak secrets outside development."""

from django.core.exceptions import ImproperlyConfigured

MIN_SECRET_KEY_LENGTH = 32
PLACEHOLDERS = ("change-me", "changeme", "insecure", "your-secret", "example")


def _is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in PLACEHOLDERS)


def validate_secrets(secret_key: str, health_password: str) -> None:
    """Raise ImproperlyConfigured for a missing, short or placeholder secret.

    An empty health password is allowed: the health endpoint then rejects every request.
    """
    if len(secret_key) < MIN_SECRET_KEY_LENGTH or _is_placeholder(secret_key):
        raise ImproperlyConfigured(
            f"SECRET_KEY must be a real secret of at least {MIN_SECRET_KEY_LENGTH} "
            "characters (no placeholder values)."
        )
    if health_password and _is_placeholder(health_password):
        raise ImproperlyConfigured(
            "HEALTH_CHECK_PASSWORD must not be a placeholder value."
        )
