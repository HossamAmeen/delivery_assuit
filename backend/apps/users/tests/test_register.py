import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.models import User
from apps.users.phone import normalize_phone

PASSWORD = "Zx9!kLm2#QwErTy"
pytestmark = pytest.mark.django_db

URLS = {
    "driver": ("register-driver", "pending_approval"),
    "trader": ("register-trader", "pending_approval"),
    "client": ("register-client", "active"),
}


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def client():
    return APIClient()


def payload(**over):
    data = {"full_name": "Ahmed Ali", "phone": "0100 123 4567", "password": PASSWORD}
    data.update(over)
    return data


def post(client, role, data, **kw):
    return client.post(reverse(URLS[role][0]), data, format="json", **kw)


@pytest.mark.parametrize("role", list(URLS))
def test_register_success(client, role):
    r = post(client, role, payload(email="a@example.com"))
    assert r.status_code == 201
    body = r.json()
    assert body["success"] is True
    user = body["data"]["user"]
    assert user["role"] == role
    assert user["status"] == URLS[role][1]
    assert user["phone"] == "01001234567"
    assert set(user) == {"id", "full_name", "phone", "role", "status"}
    assert "access" not in body["data"] and "password" not in str(body)
    assert ("pending approval" in body["message"]) == (role != "client")
    db = User.objects.get(pk=user["id"])
    assert db.username is None
    assert db.check_password(PASSWORD)
    assert db.password != PASSWORD
    assert db.is_staff is False and db.is_superuser is False


def test_two_users_without_username_and_email(client):
    assert post(client, "client", payload()).status_code == 201
    r = post(client, "client", payload(phone="0100 123 9999"))
    assert r.status_code == 201


@pytest.mark.parametrize(
    "extra",
    [
        {"role": "admin", "status": "active"},
        {"is_staff": True, "is_superuser": True, "is_active": False},
    ],
)
def test_mass_assignment_ignored(client, extra):
    r = post(client, "driver", payload(**extra))
    assert r.status_code == 201
    u = User.objects.get(pk=r.json()["data"]["user"]["id"])
    assert u.role == "driver" and u.status == "pending_approval"
    assert not u.is_staff and not u.is_superuser and u.is_active


def test_arabic_digits_phone_normalised(client):
    r = post(client, "client", payload(phone="+٢٠ ١٠٠-١٢٣-٤٥٦٧"))
    assert r.status_code == 201
    assert r.json()["data"]["user"]["phone"] == "201001234567"


def test_duplicate_phone_any_format(client):
    assert post(client, "client", payload()).status_code == 201
    r = post(client, "driver", payload(phone="+(010) 01234567"))
    assert r.status_code == 400
    body = r.json()
    assert body["success"] is False
    assert body["errors"]["phone"] == ["A user with this phone number already exists."]
    assert User.objects.count() == 1


def test_duplicate_phone_of_soft_deleted_user_is_clean_400(client):
    u = User.objects.create_account("01001234567", PASSWORD)
    u.soft_delete()
    r = post(client, "client", payload())
    assert r.status_code == 400
    assert "phone" in r.json()["errors"]


def test_duplicate_email(client):
    post(client, "client", payload(email="A@Example.com"))
    r = post(client, "client", payload(phone="01111111111", email="a@example.com"))
    assert r.status_code == 400
    assert r.json()["errors"]["email"] == ["A user with this email already exists."]


@pytest.mark.parametrize("phone", ["123", "1" * 16, "abc", ""])
def test_invalid_phone(client, phone):
    r = post(client, "client", payload(phone=phone))
    assert r.status_code == 400
    assert "phone" in r.json()["errors"]


def test_invalid_phone_message(client):
    r = post(client, "client", payload(phone="123"))
    assert r.json()["errors"]["phone"] == [
        "Enter a valid phone number (8 to 15 digits)."
    ]


def test_missing_fields(client):
    r = post(client, "client", {})
    assert r.status_code == 400
    assert set(r.json()["errors"]) == {"full_name", "phone", "password"}


def test_short_name_and_bad_email(client):
    r = post(client, "client", payload(full_name=" a ", email="nope"))
    assert set(r.json()["errors"]) == {"full_name", "email"}


@pytest.mark.parametrize("pw", ["short1!", "password", "12345678901", "Ahmed Ali"])
def test_weak_password(client, pw):
    r = post(client, "client", payload(password=pw))
    assert r.status_code == 400
    assert r.json()["errors"]["password"]
    assert User.objects.count() == 0


def test_password_similar_to_phone_rejected(client):
    r = post(client, "client", payload(phone="01001234567", password="01001234567x"))
    assert r.status_code == 400
    assert "password" in r.json()["errors"]


def test_password_not_trimmed(client):
    r = post(client, "client", payload(password="  " + PASSWORD))
    assert r.status_code == 201
    u = User.objects.get()
    assert u.check_password("  " + PASSWORD) and not u.check_password(PASSWORD)


def test_bad_authorization_header_ignored(client):
    r = post(client, "client", payload(), HTTP_AUTHORIZATION="Bearer garbage")
    assert r.status_code == 201


def test_get_not_allowed(client):
    assert client.get(reverse("register-client")).status_code == 405


def test_arabic_messages(client):
    r = post(client, "driver", payload(), HTTP_ACCEPT_LANGUAGE="ar")
    assert r.json()["message"] == "تم التسجيل بنجاح. حسابك قيد انتظار الموافقة."


def test_registered_user_can_login_when_active(client):
    post(client, "client", payload())
    r = client.post(
        reverse("token"),
        {"username_or_phone": "0100 123 4567", "password": PASSWORD},
        format="json",
    )
    assert r.status_code == 200


def test_throttled(client, settings):
    from rest_framework.throttling import SimpleRateThrottle

    rates = dict(SimpleRateThrottle.THROTTLE_RATES)
    rates["sensitive"] = "2/minute"
    SimpleRateThrottle.THROTTLE_RATES = rates
    try:
        for i in range(2):
            post(client, "client", payload(phone=f"0100000000{i}"))
        r = post(client, "client", payload(phone="01000000009"))
    finally:
        SimpleRateThrottle.THROTTLE_RATES = {**rates, "sensitive": "30/minute"}
    assert r.status_code == 429
    assert "Retry-After" in r


def test_forged_xff_does_not_bypass_throttle(client):
    from rest_framework.throttling import SimpleRateThrottle

    old = dict(SimpleRateThrottle.THROTTLE_RATES)
    SimpleRateThrottle.THROTTLE_RATES = {**old, "sensitive": "2/minute"}
    try:
        codes = [
            post(
                client,
                "client",
                payload(phone=f"0100000000{i}"),
                HTTP_X_FORWARDED_FOR=f"9.9.9.{i}",
            ).status_code
            for i in range(3)
        ]
    finally:
        SimpleRateThrottle.THROTTLE_RATES = old
    assert codes == [201, 201, 429]


def test_create_account_requires_phone():
    with pytest.raises(ValueError):
        User.objects.create_account("", PASSWORD)
    assert normalize_phone("x") == ""


def test_integrity_race_gives_validation_error(monkeypatch, client):
    from apps.users import services

    User.objects.create_account("01001234567", PASSWORD)
    monkeypatch.setattr(services, "phone_exists", lambda p: False)
    r = post(client, "client", payload())
    assert r.status_code == 400
    assert r.json()["errors"]["phone"] == [
        "A user with this phone number already exists."
    ]
