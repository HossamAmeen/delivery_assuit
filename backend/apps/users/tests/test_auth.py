import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.users.models import User

PASSWORD = "Zx9!kLm2#QwErTy"
TEST_ORIGIN = "http://localhost:5173"
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "auth-tests",
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


def login(client, ident, password=PASSWORD):
    return client.post(
        reverse("token"),
        {"username_or_phone": ident, "password": password},
        format="json",
    )


@pytest.mark.parametrize("ident", ["alice", "0100"])
def test_login_by_username_or_phone(client, user, ident):
    r = login(client, ident)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["message"] == "Login successful."
    assert set(body["data"]) == {"access", "user"}
    cookie = r.cookies["delivery_refresh"]
    assert cookie.value
    assert cookie["httponly"]
    assert cookie["samesite"] == "Strict"
    assert cookie["path"] == "/api/v1/auth/"
    assert not cookie["secure"]
    assert cookie.value not in r.content.decode()
    assert body["data"]["user"] == {
        "id": user.pk,
        "full_name": user.full_name,
        "role": "client",
        "status": "active",
    }
    assert AccessToken(body["data"]["access"])["user_id"] == str(user.pk)


@pytest.mark.parametrize(
    ("ident", "password"),
    [("alice", "wrong"), ("nobody", PASSWORD), ("0999", PASSWORD)],
)
def test_invalid_credentials_401_envelope(client, user, ident, password):
    r = login(client, ident, password)
    assert r.status_code == 401
    assert r.json() == {
        "success": False,
        "message": "Invalid credentials.",
        "errors": {},
    }


def test_inactive_and_soft_deleted_rejected(client, user):
    user.is_active = False
    user.save()
    assert login(client, "alice").status_code == 401
    user.is_active = True
    user.save()
    user.soft_delete()
    assert login(client, "alice").status_code == 401


def test_missing_fields_400(client):
    r = client.post(reverse("token"), {"username_or_phone": "x"}, format="json")
    assert r.status_code == 400
    assert r.json()["errors"]["password"] == ["This field is required."]


def test_refresh_works(client, user):
    old = login(client, "alice").cookies["delivery_refresh"].value
    r = refresh_call(client)
    assert r.status_code == 200
    assert r.json()["message"] == "Token refreshed successfully."
    assert set(r.json()["data"]) == {"access"}
    assert "refresh" not in r.json()["data"]
    assert client.cookies["delivery_refresh"].value != old
    assert AccessToken(r.json()["data"]["access"])["user_id"] == str(user.pk)


def test_refresh_ignores_json_body(client, user):
    login(client, "alice")
    r = client.post(
        reverse("token-refresh"),
        {"refresh": "junk"},
        format="json",
        HTTP_ORIGIN=TEST_ORIGIN,
    )
    assert r.status_code == 200
    assert set(r.json()["data"]) == {"access"}


def test_refresh_invalid_401_and_missing_401(client, user):
    r = refresh_call(client, "junk")
    assert r.status_code == 401
    assert r.json() == {
        "success": False,
        "message": "Token is invalid or expired.",
        "errors": {},
    }
    assert refresh_call(APIClient()).status_code == 401


def test_access_token_is_not_accepted_as_refresh(client, user):
    access = str(RefreshToken.for_user(user).access_token)
    assert refresh_call(client, access).status_code == 401


def test_rate_limit_429_after_ten(client, user, monkeypatch):
    monkeypatch.setattr(
        SimpleRateThrottle,
        "THROTTLE_RATES",
        {**SimpleRateThrottle.THROTTLE_RATES, "auth": "10/minute"},
    )
    codes = [login(client, "alice", "bad").status_code for _ in range(10)]
    assert codes == [401] * 10
    r = login(client, "alice", "bad")
    assert r.status_code == 429
    assert r.json() == {
        "success": False,
        "message": "Request rate limit exceeded.",
        "errors": {},
    }


def test_docs_and_schema_in_development(client):
    assert client.get("/api/docs/").status_code == 200
    assert client.get("/api/redoc/").status_code == 200
    r = client.get("/api/schema/?format=json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    assert "/api/v1/auth/token/" in paths
    assert "/api/v1/auth/token/refresh/" in paths
    assert "/api/v1/health/" in paths
    assert "429" in paths["/api/v1/auth/token/"]["post"]["responses"]


def test_admin_loads_with_jazzmin_for_admin_user(client):
    User.objects.create_superuser("boss", PASSWORD)
    assert client.get("/admin/").status_code == 302  # anonymous -> login
    assert client.login(username="boss", password=PASSWORD)
    r = client.get("/admin/")
    assert r.status_code == 200
    assert "jazzmin" in r.content.decode().lower()
    assert client.get("/admin/login/").status_code in (200, 302)


def test_non_staff_cannot_use_admin(client, user):
    assert client.login(username="alice", password=PASSWORD)
    r = client.get("/admin/")
    assert r.status_code == 302


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (User.Status.PENDING_APPROVAL, "account_pending"),
        (User.Status.DEACTIVATED, "account_deactivated"),
    ],
)
def test_non_active_with_correct_password_gets_403_code_no_tokens(
    client, user, status, code
):
    user.status = status
    user.save()
    for ident in ("alice", "0100"):
        r = login(client, ident)
        assert r.status_code == 403
        body = r.json()
        assert body["code"] == code
        assert body["success"] is False
        assert "data" not in body
        assert "access" not in r.content.decode()


@pytest.mark.parametrize(
    "status", [User.Status.PENDING_APPROVAL, User.Status.DEACTIVATED]
)
def test_non_active_with_wrong_password_is_generic_401(client, user, status):
    user.status = status
    user.save()
    r = login(client, "alice", "wrong-password")
    assert r.status_code == 401
    assert r.json() == {
        "success": False,
        "message": "Invalid credentials.",
        "errors": {},
    }


def test_non_active_wrong_password_identical_to_unknown_user(client, user):
    user.status = User.Status.DEACTIVATED
    user.save()
    a = login(client, "alice", "wrong-password")
    b = login(client, "ghost", "wrong-password")
    assert (a.status_code, a.json()) == (b.status_code, b.json())


def test_pending_messages_are_friendly(client, user):
    user.status = User.Status.PENDING_APPROVAL
    user.save()
    assert "pending approval" in login(client, "alice").json()["message"]
    user.status = User.Status.DEACTIVATED
    user.save()
    assert "deactivated" in login(client, "alice").json()["message"]


def test_non_active_attempts_are_throttled(client, user, monkeypatch):
    monkeypatch.setattr(
        SimpleRateThrottle,
        "THROTTLE_RATES",
        {**SimpleRateThrottle.THROTTLE_RATES, "auth": "10/minute"},
    )
    user.status = User.Status.PENDING_APPROVAL
    user.save()
    assert [login(client, "alice").status_code for _ in range(10)] == [403] * 10
    assert login(client, "alice").status_code == 429


# --- TASK-032: rotation, blacklist, logout ---------------------------------


def refresh_call(client, token=None, *, origin=TEST_ORIGIN):
    if token is not None:
        client.cookies["delivery_refresh"] = token
    extra = {"HTTP_ORIGIN": origin} if origin is not None else {}
    return client.post(reverse("token-refresh"), {}, format="json", **extra)


def logout_call(client, token=None, *, origin=TEST_ORIGIN):
    if token is not None:
        client.cookies["delivery_refresh"] = token
    extra = {"HTTP_ORIGIN": origin} if origin is not None else {}
    return client.post(reverse("logout"), {}, format="json", **extra)


def test_rotated_refresh_token_cannot_be_reused(client, user):
    old = login(client, "alice").cookies["delivery_refresh"].value
    assert refresh_call(client).status_code == 200
    new = client.cookies["delivery_refresh"].value
    assert new != old
    assert refresh_call(APIClient(), old).status_code == 401
    # Reuse revokes every outstanding refresh token of that user (VULN-017).
    assert refresh_call(APIClient(), new).status_code == 401


def test_logout_blacklists_refresh(client, user):
    token = login(client, "alice").cookies["delivery_refresh"].value
    r = logout_call(client, token)
    assert r.status_code == 200
    assert r.json() == {
        "success": True,
        "message": "Logged out successfully.",
        "data": {},
    }
    assert refresh_call(client, token).status_code == 401


def test_logout_twice_is_fine(client, user):
    token = login(client, "alice").cookies["delivery_refresh"].value
    assert logout_call(client, token).status_code == 200
    assert logout_call(client, token).status_code == 200


def test_logout_after_rotation_is_fine(client, user):
    old = login(client, "alice").cookies["delivery_refresh"].value
    refresh_call(client, old)
    assert logout_call(client, old).status_code == 200


def test_logout_expired_token_ok(client, user):
    from datetime import timedelta

    token = RefreshToken.for_user(user)
    token.set_exp(lifetime=-timedelta(minutes=1))
    assert logout_call(client, str(token)).status_code == 200


def test_logout_garbage_and_missing_are_200(client, user):
    r = logout_call(client, "junk")
    assert r.status_code == 200
    assert r.json()["message"] == "Logged out successfully."
    assert logout_call(APIClient()).status_code == 200


def test_logout_access_token_is_200(client, user):
    access = str(RefreshToken.for_user(user).access_token)
    assert logout_call(client, access).status_code == 200


def test_logout_forged_signature_is_200(client, user):
    token = str(RefreshToken.for_user(user))
    head, payload, _sig = token.split(".")
    assert logout_call(client, f"{head}.{payload}.AAAA").status_code == 200


@pytest.mark.parametrize("status", ["deactivated", "pending_approval"])
def test_inactive_status_cannot_refresh(client, user, status):
    token = login(client, "alice").cookies["delivery_refresh"].value
    user.status = status
    user.save()
    assert refresh_call(client, token).status_code == 401


def test_is_active_false_cannot_refresh(client, user):
    token = login(client, "alice").cookies["delivery_refresh"].value
    user.is_active = False
    user.save()
    assert refresh_call(client, token).status_code == 401


def test_soft_deleted_cannot_refresh(client, user):
    from django.utils import timezone

    token = login(client, "alice").cookies["delivery_refresh"].value
    User.all_objects.filter(pk=user.pk).update(deleted_at=timezone.now())
    assert refresh_call(client, token).status_code == 401


def test_logout_is_auth_throttled(client, user, monkeypatch):
    monkeypatch.setattr(
        SimpleRateThrottle,
        "THROTTLE_RATES",
        {**SimpleRateThrottle.THROTTLE_RATES, "auth": "10/minute"},
    )
    codes = [logout_call(client, "junk").status_code for _ in range(11)]
    assert codes[-1] == 429


AR = {"HTTP_ACCEPT_LANGUAGE": "ar"}


def test_pending_and_deactivated_messages_in_arabic(client, user):
    body = {"username_or_phone": "alice", "password": PASSWORD}
    user.status = User.Status.PENDING_APPROVAL
    user.save()
    r = client.post(reverse("token"), body, format="json", **AR)
    assert r.status_code == 403
    assert r.json()["message"] == (
        "حسابك قيد انتظار الموافقة. ستتمكن من تسجيل الدخول بعد موافقة المسؤول عليه."
    )
    user.status = User.Status.DEACTIVATED
    user.save()
    r = client.post(reverse("token"), body, format="json", **AR)
    assert r.status_code == 403
    assert r.json()["message"] == "تم تعطيل حسابك. يرجى التواصل مع المسؤول."


def test_logout_messages_in_arabic(client, user):
    login(client, "alice")
    r = client.post(reverse("logout"), {}, format="json", HTTP_ORIGIN=TEST_ORIGIN, **AR)
    assert r.status_code == 200
    assert r.json()["message"] == "تم تسجيل الخروج بنجاح."


# --- TASK-041: atomic rotation (VULN-011) -----------------------------------


def test_rotation_claims_token_via_blacklist_created_flag(client, user, monkeypatch):
    """Deterministic race: the token passes the up-front blacklist check, but a
    competitor blacklists it before we claim it. We must get 401, no new pair."""
    old = login(client, "alice").cookies["delivery_refresh"].value
    real_blacklist = RefreshToken.blacklist

    def competitor_wins(self):
        real_blacklist(self)  # the other request claimed it first
        return real_blacklist(self)  # our claim: created=False

    monkeypatch.setattr(RefreshToken, "blacklist", competitor_wins)
    assert refresh_call(client, old).status_code == 401


def test_rotation_db_error_is_401_not_500(client, user, monkeypatch):
    from django.db import OperationalError

    old = login(client, "alice").cookies["delivery_refresh"].value

    def boom(self):
        raise OperationalError("database is locked")

    monkeypatch.setattr(RefreshToken, "blacklist", boom)
    assert refresh_call(client, old).status_code == 401
    monkeypatch.undo()
    assert refresh_call(client, old).status_code == 200  # rolled back, still usable


@pytest.mark.django_db(transaction=True)
def test_parallel_refresh_yields_exactly_one_success(user):
    """Threaded: N parallel refreshes with one token -> one 200, rest 401, never 500.

    On SQLite (default dev DB) the strict "exactly one 200" cannot be asserted
    (see below); on PostgreSQL the row lock serialises and it is asserted. Run with
    DATABASE_URL=postgres://... to exercise that path.
    """
    import threading

    from django.db import connection, connections
    from rest_framework.test import APIClient

    old = login(APIClient(), "alice").cookies["delivery_refresh"].value
    n = 8
    barrier = threading.Barrier(n)
    codes, bodies, winner_cookies = [], [], []

    def worker():
        try:
            barrier.wait()
            r = refresh_call(APIClient(), old)
            codes.append(r.status_code)
            bodies.append(r.json())
            if r.status_code == 200 and "delivery_refresh" in r.cookies:
                winner_cookies.append(r.cookies["delivery_refresh"].value)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=worker) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert connection.vendor  # main connection still usable
    from django.core.cache import cache

    cache.clear()  # the follow-up calls below must not hit the 10/min auth throttle
    assert 500 not in codes, codes
    assert set(codes) <= {200, 401}, codes
    winners = [b for b in bodies if b.get("success")]
    assert len(winners) == codes.count(200) <= 1  # never a second valid pair
    if connection.vendor == "postgresql":
        # Row lock serialises the callers: exactly one wins.
        assert codes.count(200) == 1, codes
    # (SQLite's in-memory test DB raises "table is locked" immediately for
    # concurrent writers, so there possibly nobody wins; that is mapped to 401.)
    # Reuse of the original token is refused. When somebody won, that reuse also
    # kills the winner's new refresh token (VULN-017).
    if winners:
        assert winner_cookies
        assert "refresh" not in winners[0]["data"]
        assert refresh_call(APIClient(), old).status_code == 401
        assert refresh_call(APIClient(), winner_cookies[0]).status_code == 401
    else:
        assert refresh_call(APIClient(), old).status_code == 200  # nothing consumed


def test_refresh_and_logout_require_allowed_origin(client, user):
    login(client, "alice")
    kept = client.cookies["delivery_refresh"].value
    missing = refresh_call(client, origin=None)
    assert missing.status_code == 403
    assert missing.json()["code"] == "origin_rejected"
    assert client.cookies["delivery_refresh"].value == kept
    foreign = refresh_call(client, origin="https://evil.example")
    assert foreign.status_code == 403
    assert foreign.json()["code"] == "origin_rejected"
    blocked = logout_call(client, origin=None)
    assert blocked.status_code == 403
    assert client.cookies["delivery_refresh"].value == kept
    assert refresh_call(client).status_code == 200
