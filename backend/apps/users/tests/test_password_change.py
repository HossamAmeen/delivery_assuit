import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from apps.users.models import User

PASSWORD = "Zx9!kLm2#QwErTy"
NEW_PASSWORD = "Nw7#pQr!vB52xY"
TEST_ORIGIN = "http://localhost:5173"
AR = {"HTTP_ACCEPT_LANGUAGE": "ar"}
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "password-change-tests",
        }
    }
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user():
    return User.objects.create_user("alice", PASSWORD, phone="0100", role="client")


@pytest.fixture
def client():
    return APIClient()


def login(client, ident="alice", password=PASSWORD):
    return client.post(
        reverse("token"),
        {"username_or_phone": ident, "password": password},
        format="json",
    )


def signed_in(client):
    r = login(client)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['data']['access']}")
    return r


def change(client, current=PASSWORD, new=NEW_PASSWORD, **extra):
    return client.post(
        reverse("password-change"),
        {"current_password": current, "new_password": new},
        format="json",
        **extra,
    )


def test_success_changes_password_and_clears_cookie(client, user):
    signed_in(client)
    r = change(client)
    assert r.status_code == 200
    assert r.json() == {
        "success": True,
        "message": "Password changed. Please log in again.",
        "data": {},
    }
    assert r.cookies["delivery_refresh"].value == ""
    assert r.cookies["delivery_refresh"]["max-age"] == 0
    assert "access" not in r.json()["data"]
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)


def test_new_password_logs_in_old_does_not(client, user):
    signed_in(client)
    change(client)
    fresh = APIClient()
    assert login(fresh, password=NEW_PASSWORD).status_code == 200
    assert login(fresh, password=PASSWORD).status_code == 401


def test_all_refresh_tokens_are_revoked(client, user):
    other = APIClient()
    r1 = login(other)
    r2 = signed_in(client)
    assert OutstandingToken.objects.filter(user=user).count() == 2
    change(client)
    assert BlacklistedToken.objects.filter(token__user=user).count() == 2
    for first in (r1, r2):
        fresh = APIClient()
        r = fresh.post(
            reverse("token-refresh"),
            {},
            format="json",
            HTTP_ORIGIN=TEST_ORIGIN,
            HTTP_COOKIE=f"delivery_refresh={first.cookies['delivery_refresh'].value}",
        )
        assert r.status_code == 401


def test_other_users_tokens_are_untouched(client, user):
    bob = User.objects.create_user("bob", PASSWORD, phone="0200", role="client")
    login(APIClient(), "bob")
    signed_in(client)
    change(client)
    assert BlacklistedToken.objects.filter(token__user=bob).count() == 0


def test_wrong_current_password_is_400_and_unchanged(client, user):
    signed_in(client)
    r = change(client, current="Wrong-pass-1!")
    assert r.status_code == 400
    assert r.json() == {
        "success": False,
        "message": "Validation failed.",
        "errors": {"current_password": ["Current password is incorrect."]},
    }
    user.refresh_from_db()
    assert user.check_password(PASSWORD)
    assert BlacklistedToken.objects.count() == 0


@pytest.mark.parametrize("weak", ["123", "password", "alice1234", "0100"])
def test_weak_new_password_is_400_and_unchanged(client, user, weak):
    signed_in(client)
    r = change(client, new=weak)
    assert r.status_code == 400
    assert r.json()["errors"]["new_password"]
    user.refresh_from_db()
    assert user.check_password(PASSWORD)
    assert BlacklistedToken.objects.count() == 0


def test_wrong_current_does_not_leak_new_password_errors(client, user):
    signed_in(client)
    r = change(client, current="nope", new="123")
    assert set(r.json()["errors"]) == {"current_password"}


def test_missing_and_overlong_fields_are_400(client, user):
    signed_in(client)
    r = client.post(reverse("password-change"), {}, format="json")
    assert r.status_code == 400
    assert set(r.json()["errors"]) == {"current_password", "new_password"}
    r = change(client, new="A1!b" * 40)
    assert r.status_code == 400
    assert "new_password" in r.json()["errors"]
    r = change(client, current="x" * 129)
    assert r.status_code == 400
    assert "current_password" in r.json()["errors"]


def test_anonymous_is_401(client):
    assert change(client).status_code == 401


def test_deactivated_is_403_with_code_and_password_unchanged(client, user):
    signed_in(client)
    user.status = User.Status.DEACTIVATED
    user.save()
    r = change(client)
    assert r.status_code == 403
    assert r.json()["code"] == "account_deactivated"
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_access_token_still_works_until_expiry(client, user):
    signed_in(client)
    change(client)
    assert client.get(reverse("me")).status_code == 200


def test_messages_in_arabic(client, user):
    signed_in(client)
    r = change(client, current="Wrong-pass-1!", **AR)
    assert r.json()["errors"]["current_password"] == ["كلمة المرور الحالية غير صحيحة."]
    r = change(client, **AR)
    assert r.json()["message"] == "تم تغيير كلمة المرور. يرجى تسجيل الدخول مرة أخرى."


def test_is_throttled_with_user_scope(client, user, monkeypatch):
    from rest_framework.throttling import SimpleRateThrottle

    monkeypatch.setitem(SimpleRateThrottle.THROTTLE_RATES, "user", "2/minute")
    signed_in(client)
    codes = [change(client, current="Wrong-pass-1!").status_code for _ in range(4)]
    assert 429 in codes
