"""VULN-001: a forged X-Forwarded-For must not create a new throttle bucket."""

import pytest
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

pytestmark = [pytest.mark.django_db]

URL = "/api/v1/auth/token/"
BODY = {"username_or_phone": "nobody", "password": "x"}


@pytest.fixture(autouse=True)
def isolated(settings, monkeypatch):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "proxy-tests",
        }
    }
    from django.core.cache import cache

    cache.clear()
    monkeypatch.setattr(
        SimpleRateThrottle,
        "THROTTLE_RATES",
        {**SimpleRateThrottle.THROTTLE_RATES, "auth": "10/minute"},
    )
    yield
    cache.clear()


def attempts(n, forwarded):
    client = APIClient()
    codes = []
    for i in range(n):
        extra = {"HTTP_X_FORWARDED_FOR": forwarded(i)} if forwarded else {}
        codes.append(client.post(URL, BODY, format="json", **extra).status_code)
    return codes


def set_proxies(settings, value):
    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "NUM_PROXIES": value}


def test_default_is_no_trusted_proxy(settings):
    assert settings.REST_FRAMEWORK["NUM_PROXIES"] == 0


def test_rotating_forwarded_header_is_throttled_with_no_proxy(settings):
    set_proxies(settings, 0)
    codes = attempts(30, lambda i: f"172.16.0.{i}")
    assert codes[:10] == [401] * 10
    assert codes[10:] == [429] * 20


def test_without_header_still_throttled(settings):
    set_proxies(settings, 0)
    codes = attempts(12, None)
    assert codes[10:] == [429, 429]


def test_one_trusted_proxy_uses_the_last_hop_not_client_supplied_prefix(settings):
    set_proxies(settings, 1)
    # Client prepends fake addresses; the proxy appends the real one (203.0.113.9).
    codes = attempts(30, lambda i: f"10.0.0.{i}, 203.0.113.9")
    assert codes[:10] == [401] * 10
    assert codes[10:] == [429] * 20


def test_one_trusted_proxy_separates_real_clients(settings):
    set_proxies(settings, 1)
    attempts(10, lambda i: "198.51.100.1")
    other = attempts(1, lambda i: "198.51.100.2")
    assert other == [401]


def test_health_limit_also_not_dodged(settings, monkeypatch):
    set_proxies(settings, 0)
    settings.HEALTH_CHECK_PASSWORD = "pw"
    monkeypatch.setattr(
        SimpleRateThrottle,
        "THROTTLE_RATES",
        {**SimpleRateThrottle.THROTTLE_RATES, "health": "5/minute"},
    )
    client = APIClient()
    codes = [
        client.get(
            "/api/v1/health/",
            HTTP_X_HEALTH_CHECK_TOKEN="pw",
            HTTP_X_FORWARDED_FOR=f"9.9.9.{i}",
        ).status_code
        for i in range(8)
    ]
    assert codes[:5] == [200] * 5
    assert codes[5:] == [429] * 3
