import re
from datetime import timedelta

import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from apps.users.models import PasswordResetToken, User

PASSWORD = "Zx9!kLm2#QwErTy"
NEW_PASSWORD = "Nw7#pQr!vB52xY"
TEST_ORIGIN = "http://localhost:5173"
AR = {"HTTP_ACCEPT_LANGUAGE": "ar"}
SAME_MESSAGE = "If an email is on file for that account, a reset link has been sent."
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated(settings, monkeypatch):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "reset-tests",
        }
    }
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.FRONTEND_ORIGIN = "http://localhost:5173"
    monkeypatch.setitem(SimpleRateThrottle.THROTTLE_RATES, "recovery", "1000/hour")
    monkeypatch.setitem(
        SimpleRateThrottle.THROTTLE_RATES, "recovery_identifier", "1000/hour"
    )
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user():
    return User.objects.create_account(
        "01001234567",
        PASSWORD,
        full_name="Ahmed Ali",
        email="ahmed@example.com",
        role="client",
    )


@pytest.fixture
def client():
    return APIClient()


def ask(client, identifier, **extra):
    return client.post(
        reverse("password-reset"), {"identifier": identifier}, format="json", **extra
    )


def confirm(client, token, password=NEW_PASSWORD, **extra):
    return client.post(
        reverse("password-reset-confirm"),
        {"token": token, "new_password": password},
        format="json",
        **extra,
    )


def sent_token():
    assert len(mail.outbox) >= 1
    m = re.search(r"token=([\w-]+)", mail.outbox[-1].body)
    return m.group(1)


def login(client, ident, password):
    return client.post(
        reverse("token"),
        {"username_or_phone": ident, "password": password},
        format="json",
    )


# --- request -----------------------------------------------------------------


@pytest.mark.parametrize(
    "identifier", ["01001234567", "0100 123 4567", "AHMED@Example.com"]
)
def test_known_account_gets_one_email_with_link(client, user, identifier):
    r = ask(client, identifier)
    assert r.status_code == 200
    assert r.json() == {"success": True, "message": SAME_MESSAGE, "data": {}}
    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert msg.to == ["ahmed@example.com"]
    assert re.search(
        r"http://localhost:5173/reset-password\?token=[\w-]{20,}", msg.body
    )


def test_username_identifier_works(client):
    User.objects.create_user("bob", PASSWORD, email="bob@example.com")
    ask(client, "bob")
    assert len(mail.outbox) == 1


def test_response_body_identical_for_unknown_no_email_and_sent(client, user):
    no_email = User.objects.create_account("01002223344", PASSWORD, role="client")
    assert no_email.email == ""
    bodies = [
        ask(client, "01001234567"),
        ask(client, "01009998888"),
        ask(client, "01002223344"),
        ask(client, "ghost-user"),
        ask(client, "ghost@example.com"),
    ]
    assert {r.status_code for r in bodies} == {200}
    assert len({r.content for r in bodies}) == 1
    assert len(mail.outbox) == 1


def test_token_never_in_response_and_only_hash_stored(client, user):
    r = ask(client, "01001234567")
    raw = sent_token()
    assert raw not in r.content.decode()
    row = PasswordResetToken.objects.get()
    assert row.token_hash != raw
    assert raw not in row.token_hash
    assert len(row.token_hash) == 64
    assert row.expires_at - row.created_at <= timedelta(minutes=30, seconds=5)
    assert row.expires_at - row.created_at >= timedelta(minutes=29)


def test_soft_deleted_account_is_unknown(client, user):
    user.soft_delete()
    user.save()
    ask(client, "01001234567")
    ask(client, "ahmed@example.com")
    assert mail.outbox == []
    assert PasswordResetToken.objects.count() == 0


def test_username_that_looks_like_digits_is_not_matched_as_phone(client, user):
    ask(client, "abc01001234567")
    assert mail.outbox == []


def test_new_request_invalidates_previous_link(client, user):
    ask(client, "01001234567")
    first = sent_token()
    ask(client, "01001234567")
    second = sent_token()
    assert first != second
    assert confirm(client, first).status_code == 400
    assert confirm(client, second).status_code == 200


def test_blank_and_overlong_identifier_400(client):
    assert ask(client, "").status_code == 400
    assert ask(client, "   ").status_code == 400
    r = ask(client, "x" * 255)
    assert r.status_code == 400
    assert "identifier" in r.json()["errors"]
    assert client.post(reverse("password-reset"), {}, format="json").status_code == 400


def test_mail_failure_does_not_change_the_answer(client, user, monkeypatch):
    def boom(*a, **k):
        raise OSError("smtp down")

    monkeypatch.setattr("apps.users.services.send_mail", boom)
    r = ask(client, "01001234567")
    assert r.status_code == 200
    assert r.json()["message"] == SAME_MESSAGE


def test_email_and_message_in_arabic(client, user):
    r = ask(client, "01001234567", **AR)
    assert r.json()["message"].startswith("إذا كان")
    assert mail.outbox[0].subject == "إعادة تعيين كلمة المرور"
    assert "reset-password?token=" in mail.outbox[0].body


# --- confirm -----------------------------------------------------------------


def test_confirm_sets_password_and_burns_token(client, user):
    ask(client, "01001234567")
    token = sent_token()
    r = confirm(client, token)
    assert r.status_code == 200
    assert r.json() == {
        "success": True,
        "message": "Password has been reset. Please log in.",
        "data": {},
    }
    assert "access" not in r.content.decode()
    assert login(client, "01001234567", NEW_PASSWORD).status_code == 200
    assert login(client, "01001234567", PASSWORD).status_code == 401
    again = confirm(client, token, password="An0ther!Pass77x")
    assert again.status_code == 400
    assert again.json()["errors"] == {
        "token": ["This reset link is invalid or has expired."]
    }


def test_confirm_revokes_refresh_tokens_and_clears_cookie(client, user):
    r = login(client, "01001234567", PASSWORD)
    old_cookie = r.cookies["delivery_refresh"].value
    ask(client, "01001234567")
    token = sent_token()
    c = APIClient()
    c.cookies["delivery_refresh"] = old_cookie
    r = confirm(c, token)
    assert r.status_code == 200
    assert r.cookies["delivery_refresh"]["max-age"] == 0
    fresh = APIClient()
    r = fresh.post(
        reverse("token-refresh"),
        {},
        format="json",
        HTTP_ORIGIN=TEST_ORIGIN,
        HTTP_COOKIE=f"delivery_refresh={old_cookie}",
    )
    assert r.status_code == 401


def test_no_cookie_set_when_request_had_none(client, user):
    ask(client, "01001234567")
    r = confirm(client, sent_token())
    assert "delivery_refresh" not in r.cookies


def test_weak_password_rejected_and_token_still_valid(client, user):
    ask(client, "01001234567")
    token = sent_token()
    r = confirm(client, token, password="123")
    assert r.status_code == 400
    assert r.json()["errors"]["new_password"]
    assert PasswordResetToken.objects.get().used_at is None
    user.refresh_from_db()
    assert user.check_password(PASSWORD)
    assert confirm(client, token).status_code == 200


def test_expired_unknown_and_used_share_one_message(client, user):
    ask(client, "01001234567")
    token = sent_token()
    PasswordResetToken.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    expired = confirm(client, token)
    unknown = confirm(client, "not-a-real-token")
    assert expired.status_code == unknown.status_code == 400
    assert expired.content == unknown.content
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_weak_password_with_bad_token_says_token(client, user):
    r = confirm(client, "nope", password="123")
    assert set(r.json()["errors"]) == {"token"}


def test_missing_and_overlong_fields_400(client):
    r = client.post(reverse("password-reset-confirm"), {}, format="json")
    assert set(r.json()["errors"]) == {"token", "new_password"}
    assert confirm(client, "t", password="A1!b" * 40).status_code == 400


def test_other_users_tokens_untouched(client, user):
    other = User.objects.create_account(
        "01005556677", PASSWORD, email="other@example.com"
    )
    ask(client, "01005556677")
    other_token = sent_token()
    ask(client, "01001234567")
    confirm(client, sent_token())
    assert confirm(client, other_token).status_code == 200
    other.refresh_from_db()
    assert other.check_password(NEW_PASSWORD)


def test_deactivated_account_can_reset_but_cannot_log_in(client, user):
    user.status = User.Status.DEACTIVATED
    user.save()
    ask(client, "01001234567")
    assert confirm(client, sent_token()).status_code == 200
    assert login(client, "01001234567", NEW_PASSWORD).status_code == 403


def test_two_confirms_with_one_token_only_one_wins(user, monkeypatch):
    """The claim is a conditional UPDATE: the loser of a race gets the token error."""
    from apps.users import services

    ask(APIClient(), "01001234567")
    token = sent_token()
    real = services._find_valid_reset_token
    row = real(token)
    monkeypatch.setattr(services, "_find_valid_reset_token", lambda raw: row)
    assert confirm(APIClient(), token).status_code == 200
    r = confirm(APIClient(), token, password="An0ther!Pass77x")
    assert r.status_code == 400
    assert "token" in r.json()["errors"]


# --- throttling --------------------------------------------------------------


def test_sixth_request_from_one_ip_is_429(client, monkeypatch):
    monkeypatch.setitem(SimpleRateThrottle.THROTTLE_RATES, "recovery", "5/hour")
    codes = [ask(client, f"user{i}").status_code for i in range(6)]
    assert codes == [200, 200, 200, 200, 200, 429]


def test_sixth_request_for_one_identifier_is_429_even_from_new_ips(client, monkeypatch):
    monkeypatch.setitem(
        SimpleRateThrottle.THROTTLE_RATES, "recovery_identifier", "5/hour"
    )
    codes = [
        ask(client, "0100-123-4567", REMOTE_ADDR=f"10.0.0.{i}").status_code
        for i in range(5)
    ]
    assert codes == [200] * 5
    assert ask(client, "01001234567", REMOTE_ADDR="10.0.0.99").status_code == 429
    assert ask(client, "01009990000", REMOTE_ADDR="10.0.0.99").status_code == 200


def test_confirm_is_throttled_per_ip(client, monkeypatch):
    monkeypatch.setitem(SimpleRateThrottle.THROTTLE_RATES, "recovery", "3/hour")
    codes = [confirm(client, "x").status_code for _ in range(4)]
    assert codes == [400, 400, 400, 429]


def test_default_rates_are_five_per_hour():
    """Read the defaults in a clean process (the fixture above edits the live dict)."""
    import os
    import subprocess
    import sys

    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("RATELIMIT_", "PASSWORD_RESET"))
    }
    env |= {
        "DJANGO_SETTINGS_MODULE": "config.settings.development",
        "SECRET_KEY": "x" * 50,
    }
    out = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from django.conf import settings as s;"
                "r=s.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'];"
                "print(r['recovery'], r['recovery_identifier'],"
                " s.PASSWORD_RESET_TIMEOUT_MINUTES)"
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert out == ["5/hour", "5/hour", "30"]
