from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AuthRateThrottle(UserRateThrottle):
    """Strict limit for token endpoints (keyed by user, or IP when anonymous)."""

    scope = "auth"


class SensitiveRateThrottle(UserRateThrottle):
    """OTP, password reset, payments and other sensitive operations."""

    scope = "sensitive"


class HealthRateThrottle(AnonRateThrottle):
    """Separate bucket per client IP so deploy checks are not starved."""

    scope = "health"
