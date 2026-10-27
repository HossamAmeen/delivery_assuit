import pytest
from django.core.cache import cache
from django.test import Client

from apps.users.models import User

pytestmark = pytest.mark.django_db
URL = "/admin/login/"
GOOD = "Zx9!kLm2#QwErTy"


@pytest.fixture(autouse=True)
def _setup(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "admin-throttle-tests",
        }
    }
    settings.ADMIN_LOGIN_MAX_ATTEMPTS = 5
    settings.ADMIN_LOGIN_MAX_ATTEMPTS_PER_USERNAME = 8
    settings.ADMIN_LOGIN_WINDOW_SECONDS = 900
    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "NUM_PROXIES": 0}
    cache.clear()
    User.objects.create_superuser("boss", GOOD)
    yield
    cache.clear()


def post(client, username="boss", password="bad", **extra):
    return client.post(
        URL,
        {"username": username, "password": password, "next": "/admin/"},
        **extra,
    )


def test_five_failures_are_processed_then_blocked():
    c = Client()
    assert [post(c).status_code for _ in range(5)] == [200] * 5
    r = post(c)
    assert r.status_code == 429
    assert r["Retry-After"] == "900"


def test_correct_password_is_also_refused_while_locked():
    c = Client()
    for _ in range(5):
        post(c)
    assert post(c, password=GOOD).status_code == 429


def test_other_ip_is_not_affected():
    c = Client()
    for _ in range(6):
        post(c, REMOTE_ADDR="10.0.0.1")
    assert post(c, password=GOOD, REMOTE_ADDR="10.0.0.2").status_code == 302


def test_forged_forwarded_header_does_not_reset_the_limit():
    c = Client()
    codes = [post(c, HTTP_X_FORWARDED_FOR=f"1.2.3.{i}").status_code for i in range(8)]
    assert codes[:5] == [200] * 5
    assert codes[5:] == [429] * 3


def test_success_clears_the_counters():
    c = Client()
    for _ in range(4):
        post(c)
    assert post(c, password=GOOD).status_code == 302
    assert [post(Client()).status_code for _ in range(5)] == [200] * 5


def test_per_username_backstop_across_many_ips():
    c = Client()
    codes = [post(c, REMOTE_ADDR=f"10.1.0.{i}").status_code for i in range(10)]
    assert codes[:8] == [200] * 8
    assert codes[8:] == [429, 429]
    # a different username from a fresh IP is fine
    assert post(c, username="someone", REMOTE_ADDR="10.9.9.9").status_code == 200


def test_get_and_other_paths_are_not_throttled():
    c = Client()
    for _ in range(6):
        post(c)
    assert c.get(URL).status_code == 200
    other = c.post("/api/v1/auth/token/", {}, content_type="application/json")
    assert other.status_code == 400  # validation error, not the admin lockout


def test_counter_window_expires(monkeypatch):
    import time as real_time

    now = [real_time.time()]
    monkeypatch.setattr("django.core.cache.backends.locmem.time.time", lambda: now[0])
    c = Client()
    for _ in range(5):
        post(c)
    assert post(c).status_code == 429
    now[0] += 901  # past the 900 s window
    assert post(c).status_code == 200


def test_blocked_message_is_translated():
    c = Client()
    for _ in range(5):
        post(c)
    r = post(c, HTTP_ACCEPT_LANGUAGE="ar")
    assert r.status_code == 429
    assert "محاولات" in r.content.decode()


def test_admin_login_without_next_lands_on_the_admin_not_a_404():
    """BUG-006: the Jazzmin form sends no `next`, which used to redirect to /accounts/profile/."""
    c = Client()
    r = c.post(URL, {"username": "boss", "password": GOOD})
    assert r.status_code == 302
    assert r["Location"] == "/admin/"
    assert c.get(r["Location"]).status_code == 200
