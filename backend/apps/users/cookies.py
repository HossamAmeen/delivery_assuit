"""HttpOnly refresh cookie and the Origin check for refresh and logout."""

from django.conf import settings

REFRESH_COOKIE_NAME = "delivery_refresh"
REFRESH_COOKIE_PATH = "/api/v1/auth/"


def refresh_cookie(request) -> str:
    return request.COOKIES.get(REFRESH_COOKIE_NAME, "")


def set_refresh_cookie(response, raw_refresh: str) -> None:
    lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        raw_refresh,
        max_age=int(lifetime.total_seconds()),
        path=REFRESH_COOKIE_PATH,
        secure=settings.REFRESH_COOKIE_SECURE,
        httponly=True,
        samesite="Strict",
    )


def clear_refresh_cookie(response) -> None:
    # Set the same flags as ``set_refresh_cookie``. ``delete_cookie`` on this
    # Django cannot mark the clearing header ``Secure``, so a Secure cookie
    # would otherwise stay in the browser.
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        "",
        max_age=0,
        path=REFRESH_COOKIE_PATH,
        secure=settings.REFRESH_COOKIE_SECURE,
        httponly=True,
        samesite="Strict",
        expires="Thu, 01 Jan 1970 00:00:00 GMT",
    )


def origin_allowed(request) -> bool:
    """True when ``Origin`` is present and exactly one of ``CORS_ALLOWED_ORIGINS``."""
    origin = request.META.get("HTTP_ORIGIN", "")
    return bool(origin) and origin in settings.CORS_ALLOWED_ORIGINS
