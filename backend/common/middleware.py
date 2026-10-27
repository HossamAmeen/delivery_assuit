"""Brute-force protection for the Django admin login page (VULN-003).

Failed POSTs to the admin login are counted in the shared cache, per client IP and per
username. When a limit is reached the request is refused with 429 before any password is
checked, so even the correct password is rejected until the window ends. A successful login
clears the counters for that IP and username.

The IP comes from DRF's ``get_ident`` and therefore honours ``NUM_PROXIES`` (see VULN-001).
A per-username cap is a backstop against distributed guessing; it can also lock a real admin
out for the window, which is the accepted trade-off (they can use a different account or wait).
"""

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext as _
from rest_framework.throttling import BaseThrottle

_IP = "admin-login:ip:{}"
_USER = "admin-login:user:{}"


def _count(key):
    return cache.get(key, 0)


def _incr(key, window):
    # add() sets the expiry only when the key is new, giving a fixed window.
    if cache.add(key, 1, timeout=window):
        return 1
    try:
        return cache.incr(key)
    except ValueError:  # expired between add() and incr()
        cache.set(key, 1, timeout=window)
        return 1


class AdminLoginThrottleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def _login_path(self):
        try:
            return reverse("admin:login")
        except NoReverseMatch:  # admin not installed
            return None

    def __call__(self, request):
        if request.method != "POST" or request.path != self._login_path():
            return self.get_response(request)

        max_ip = settings.ADMIN_LOGIN_MAX_ATTEMPTS
        max_user = settings.ADMIN_LOGIN_MAX_ATTEMPTS_PER_USERNAME
        window = settings.ADMIN_LOGIN_WINDOW_SECONDS
        ip = BaseThrottle().get_ident(request)
        username = (request.POST.get("username") or "").strip().lower()[:150]
        ip_key, user_key = _IP.format(ip), _USER.format(username)

        if _count(ip_key) >= max_ip or (username and _count(user_key) >= max_user):
            response = HttpResponse(
                _("Too many failed login attempts. Try again later."),
                status=429,
                content_type="text/plain; charset=utf-8",
            )
            response["Retry-After"] = str(window)
            return response

        response = self.get_response(request)
        if response.status_code == 302:  # successful login redirects
            cache.delete_many([ip_key, user_key])
        elif response.status_code == 200:  # form re-rendered with errors
            _incr(ip_key, window)
            if username:
                _incr(user_key, window)
        return response


NO_STORE_PREFIXES = ("/api/v1/auth/", "/api/v1/users/")


class NoStoreMiddleware:
    """Auth and user-management responses carry tokens and personal data: never cache them (VULN-019)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(NO_STORE_PREFIXES):
            response["Cache-Control"] = "no-store"
        return response
