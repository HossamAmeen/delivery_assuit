"""TASK-053: VULN-014, VULN-015, VULN-016, VULN-019."""

from unittest import mock

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.users.models import User

from .conftest import PASSWORD, client_for, make_user

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_cache(settings, monkeypatch):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "hardening-tests",
        }
    }
    from rest_framework.throttling import SimpleRateThrottle

    for scope in ("auth", "recovery", "recovery_identifier", "sensitive"):
        monkeypatch.setitem(SimpleRateThrottle.THROTTLE_RATES, scope, "1000/hour")
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


def login(ident, password=PASSWORD, **extra):
    return APIClient().post(
        reverse("token"),
        {"username_or_phone": ident, "password": password},
        format="json",
        **extra,
    )


# --- VULN-019: Cache-Control: no-store -----------------------------------------


def test_auth_responses_are_no_store():
    user = make_user("alice", "client", "01011112222", email="a@example.com")
    c = client_for(user)
    plain = APIClient()
    origin = {"HTTP_ORIGIN": "http://localhost:5173"}
    calls = [
        login("alice"),
        plain.post(reverse("token-refresh"), {}, format="json", **origin),
        plain.post(reverse("logout"), {}, format="json", **origin),
        plain.post(
            reverse("register-client"),
            {"full_name": "New Person", "phone": "01099998888", "password": PASSWORD},
            format="json",
        ),
        c.get(reverse("me")),
        c.patch(reverse("me"), {"full_name": "Alice B"}, format="json"),
        c.post(
            reverse("password-change"),
            {"current_password": "wrong", "new_password": "x"},
            format="json",
        ),
        plain.post(reverse("password-reset"), {"identifier": "alice"}, format="json"),
        plain.post(
            reverse("password-reset-confirm"),
            {"token": "t", "new_password": "x"},
            format="json",
        ),
        login("alice", "wrong"),
        APIClient().get(reverse("me")),
    ]
    for r in calls:
        assert r["Cache-Control"] == "no-store", r.request["PATH_INFO"]


def test_user_management_responses_are_no_store(admin_client):
    assert admin_client.get(reverse("user-list"))["Cache-Control"] == "no-store"


def test_health_is_not_marked_no_store():
    r = APIClient().get("/api/v1/health/")
    assert r.get("Cache-Control") != "no-store"


# --- VULN-015: lengths ---------------------------------------------------------


def test_two_megabyte_password_is_400_and_never_hashed():
    make_user("alice", "client", "01011112222")
    with (
        mock.patch("apps.users.services.check_password") as dummy,
        mock.patch.object(User, "check_password") as real,
    ):
        r = login("alice", "p" * 2_000_000)
    assert r.status_code == 400
    assert r.json()["errors"]["password"] == [
        "Ensure this field has no more than 128 characters."
    ]
    dummy.assert_not_called()
    real.assert_not_called()


def test_long_identifier_is_400_and_never_hashed():
    with mock.patch("apps.users.services.check_password") as dummy:
        r = login("x" * 151)
    assert r.status_code == 400
    assert r.json()["errors"]["username_or_phone"] == [
        "Ensure this field has no more than 150 characters."
    ]
    dummy.assert_not_called()


def test_limits_are_inclusive():
    make_user("alice", "client", "01011112222")
    assert login("alice", "p" * 128).status_code == 401
    assert login("x" * 150).status_code == 401


# --- VULN-016: phone vs username -----------------------------------------------


def test_prefixed_letters_do_not_authenticate_as_phone():
    make_user("alice", "client", "01000000005")
    assert login("01000000005").status_code == 200
    r = login("x01000000005")
    assert r.status_code == 401
    assert r.json()["message"] == "Invalid credentials."
    assert login("01000000005abc").status_code == 401
    assert login("tel:01000000005").status_code == 401


@pytest.mark.parametrize(
    "ident",
    [
        "0100 000 0005",
        "0100-000-0005",
        "+0100 000 0005",
        "(0100) 000-0005",
        "٠١٠٠٠٠٠٠٠٠٥",
    ],
)
def test_phone_formats_still_work(ident):
    make_user("alice", "client", "01000000005")
    assert login(ident).status_code == 200


def test_exact_username_is_case_sensitive_and_trimmed():
    make_user("Alice", "client", "01011112222")
    assert login("Alice").status_code == 200
    assert login("  Alice  ").status_code == 200
    assert login("alice").status_code == 401


def test_username_that_looks_like_a_phone_wins():
    victim = make_user("01000000005", "client", "01099990000")
    make_user("someone", "client", "01000000005")
    r = login("01000000005")
    assert r.status_code == 200
    assert r.json()["data"]["user"]["id"] == victim.pk


def test_recovery_lookup_follows_the_same_rule():
    from apps.users import services

    make_user("alice", "client", "01000000005", email="a@example.com")
    assert services.find_user_for_recovery("x01000000005") is None
    assert services.find_user_for_recovery("0100 000 0005").username == "alice"


# --- VULN-014: bodies that used to be 500 ---------------------------------------


def test_deeply_nested_json_is_400_not_500():
    body = "[" * 100_000 + "]" * 100_000
    r = APIClient().post(reverse("token"), body, content_type="application/json")
    assert r.status_code == 400
    assert r.json() == {
        "success": False,
        "message": "Validation failed.",
        "errors": {"non_field_errors": ["Invalid JSON."]},
    }


def test_deeply_nested_json_object_is_400():
    body = '{"a":' * 100_000 + "1" + "}" * 100_000
    r = APIClient().post(reverse("token"), body, content_type="application/json")
    assert r.status_code == 400


def test_plain_invalid_json_is_400_with_same_body():
    r = APIClient().post(reverse("token"), "{nope", content_type="application/json")
    assert r.status_code == 400
    assert r.json()["errors"] == {"non_field_errors": ["Invalid JSON."]}


def test_oversize_body_is_413_not_500(settings):
    settings.DATA_UPLOAD_MAX_MEMORY_SIZE = 1000
    body = '{"username_or_phone": "a", "password": "' + "p" * 5000 + '"}'
    r = APIClient().post(reverse("token"), body, content_type="application/json")
    assert r.status_code == 413
    assert r.json() == {
        "success": False,
        "message": "Request body is too large.",
        "errors": {},
    }


def test_normal_body_under_the_limit_still_works():
    make_user("alice", "client", "01011112222")
    assert login("alice").status_code == 200


def test_signed_token_with_non_integer_user_id_is_401():
    user = make_user("alice", "client", "01011112222")
    for bad in (
        "abc",
        "1; DROP TABLE users",
        "",
        None,
        [1],
        {"a": 1},
        True,
        "1.5",
        "١٢",
    ):
        token = AccessToken.for_user(user)
        token["user_id"] = bad
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        r = c.get(reverse("me"))
        assert r.status_code == 401, bad
        assert r.json()["success"] is False


def test_signed_token_with_valid_user_id_still_works():
    user = make_user("alice", "client", "01011112222")
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    assert c.get(reverse("me")).status_code == 200
    token = AccessToken.for_user(user)
    token["user_id"] = user.pk  # an int claim is fine too
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert c.get(reverse("me")).status_code == 200


def test_unrelated_errors_keep_the_generic_500_body(monkeypatch):
    from django.test import Client

    def boom(*a, **k):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr("apps.users.views.services.authenticate_user", boom)
    r = Client(raise_request_exception=False).post(
        reverse("token"),
        '{"username_or_phone": "a", "password": "b"}',
        content_type="application/json",
    )
    assert r.status_code == 500
    assert b"secret internal detail" not in r.content
    assert r.json()["message"] == "An unexpected error occurred."
