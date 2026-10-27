import threading

import pytest
from django.db import IntegrityError, connection, transaction
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.models import User

PASSWORD = "Zx9!kLm2#QwErTy"
AR = {"HTTP_ACCEPT_LANGUAGE": "ar"}
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "profile-tests",
        }
    }
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user():
    return User.objects.create_account(
        "01001234567", PASSWORD, full_name="Ahmed Ali", role="client"
    )


@pytest.fixture
def other():
    return User.objects.create_account(
        "01002223344",
        PASSWORD,
        full_name="Sara Omar",
        email="sara@example.com",
        role="client",
    )


@pytest.fixture
def client(user):
    c = APIClient()
    r = c.post(
        reverse("token"),
        {"username_or_phone": "01001234567", "password": PASSWORD},
        format="json",
    )
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['data']['access']}")
    return c


def patch(client, body, **extra):
    return client.patch(reverse("me"), body, format="json", **extra)


def test_get_shows_profile_fields(client, user):
    data = client.get(reverse("me")).json()["data"]["user"]
    assert data == {
        "id": user.id,
        "full_name": "Ahmed Ali",
        "phone": "01001234567",
        "username": None,
        "email": "",
        "role": "client",
        "status": "active",
        "rejection_reason": "",
    }


def test_update_name_phone_email(client, user):
    r = patch(
        client,
        {
            "full_name": "  Ahmed Z  ",
            "phone": "٠١٠٠ 555 6677",
            "email": " A@Example.COM ",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "Profile updated."
    assert body["data"]["user"]["full_name"] == "Ahmed Z"
    assert body["data"]["user"]["phone"] == "01005556677"
    assert body["data"]["user"]["email"] == "a@example.com"
    user.refresh_from_db()
    assert (user.full_name, user.phone, user.email) == (
        "Ahmed Z",
        "01005556677",
        "a@example.com",
    )


def test_partial_and_empty_patch(client, user):
    assert patch(client, {"full_name": "New Name"}).status_code == 200
    user.refresh_from_db()
    assert user.full_name == "New Name"
    assert user.phone == "01001234567"
    assert patch(client, {}).status_code == 200


def test_email_can_be_cleared(client, user):
    patch(client, {"email": "a@example.com"})
    r = patch(client, {"email": ""})
    assert r.status_code == 200
    assert r.json()["data"]["user"]["email"] == ""


def test_keeping_own_phone_and_email_is_not_a_duplicate(client, user):
    patch(client, {"email": "a@example.com"})
    r = patch(client, {"phone": "0100-123-4567", "email": "A@example.com"})
    assert r.status_code == 200


def test_duplicate_phone_and_email_rejected(client, user, other):
    r = patch(client, {"phone": "0100 222 3344"})
    assert r.status_code == 400
    assert r.json()["errors"] == {
        "phone": ["A user with this phone number already exists."]
    }
    r = patch(client, {"email": "SARA@example.com"})
    assert r.status_code == 400
    assert r.json()["errors"] == {"email": ["A user with this email already exists."]}
    user.refresh_from_db()
    assert user.email == ""


def test_soft_deleted_phone_still_taken_but_email_is_free(client, user, other):
    other.soft_delete()
    other.save()
    assert patch(client, {"phone": "01002223344"}).status_code == 400
    assert patch(client, {"email": "sara@example.com"}).status_code == 200


@pytest.mark.parametrize(
    "body,field",
    [
        ({"full_name": "A"}, "full_name"),
        ({"full_name": "x" * 256}, "full_name"),
        ({"full_name": "   "}, "full_name"),
        ({"phone": "123"}, "phone"),
        ({"phone": "abc"}, "phone"),
        ({"phone": ""}, "phone"),
        ({"email": "not-an-email"}, "email"),
    ],
)
def test_invalid_values_400(client, user, body, field):
    r = patch(client, body)
    assert r.status_code == 400
    assert field in r.json()["errors"]
    user.refresh_from_db()
    assert user.full_name == "Ahmed Ali"


def test_forbidden_fields_rejected_and_nothing_saved(client, user):
    r = patch(
        client,
        {"full_name": "Hacker", "role": "admin", "status": "active", "username": "x"},
    )
    assert r.status_code == 400
    assert r.json() == {
        "success": False,
        "message": "Validation failed.",
        "errors": {
            "role": ["You cannot change this field."],
            "status": ["You cannot change this field."],
            "username": ["You cannot change this field."],
        },
    }
    user.refresh_from_db()
    assert (user.full_name, user.role, user.username) == ("Ahmed Ali", "client", None)


def test_forbidden_field_merges_with_field_errors(client):
    r = patch(client, {"phone": "1", "role": "admin"})
    assert set(r.json()["errors"]) == {"phone", "role"}


def test_mass_assignment_other_fields_ignored(client, user):
    r = patch(
        client,
        {"full_name": "Ok Name", "is_staff": True, "id": 999, "is_superuser": True},
    )
    assert r.status_code == 200
    user.refresh_from_db()
    assert not user.is_staff
    assert not user.is_superuser
    assert user.id != 999


def test_only_own_row_is_touched(client, user, other):
    patch(client, {"full_name": "Changed Me"})
    other.refresh_from_db()
    assert other.full_name == "Sara Omar"


def test_anonymous_401_and_deactivated_403(user):
    c = APIClient()
    assert c.patch(reverse("me"), {}, format="json").status_code == 401


def test_deactivated_403(client, user):
    user.status = User.Status.DEACTIVATED
    user.save()
    r = patch(client, {"full_name": "Nope Nope"})
    assert r.status_code == 403
    assert r.json()["code"] == "account_deactivated"
    user.refresh_from_db()
    assert user.full_name == "Ahmed Ali"


def test_messages_in_arabic(client):
    r = patch(client, {"role": "admin"}, **AR)
    assert r.json()["errors"]["role"] == ["لا يمكنك تغيير هذا الحقل."]
    r = patch(client, {"full_name": "Ahmed Z"}, **AR)
    assert r.json()["message"] == "تم تحديث الملف الشخصي."


def test_db_constraint_blocks_emails_differing_only_by_case(user, other):
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.filter(pk=user.pk).update(email="SARA@EXAMPLE.com")


def test_db_constraint_allows_many_empty_emails(user, other):
    other.email = ""
    other.save()
    assert User.objects.filter(email="").count() == 2


def _miss_once(monkeypatch, services):
    """The first email lookup (validation) misses, as if the rival committed later."""
    real = services.email_exists
    calls = []

    def fake(*a, **k):
        calls.append(1)
        return False if len(calls) == 1 else real(*a, **k)

    monkeypatch.setattr(services, "email_exists", fake)


def test_integrity_race_maps_to_400(client, user, other, monkeypatch):
    """A concurrent winner after validation passes surfaces as a 400, not a 500."""
    from apps.users import services

    _miss_once(monkeypatch, services)
    r = patch(client, {"email": "Sara@Example.com"})
    assert r.status_code == 400
    assert r.json()["errors"] == {"email": ["A user with this email already exists."]}


def test_register_email_race_maps_to_email_error(monkeypatch):
    from apps.users import serializers as ser

    User.objects.create_account("01009998877", PASSWORD, email="dup@example.com")
    _miss_once(monkeypatch, ser.services)
    r = APIClient().post(
        reverse("register-client"),
        {
            "full_name": "Dup Email",
            "phone": "01009990000",
            "password": PASSWORD,
            "email": "DUP@example.com",
        },
        format="json",
    )
    assert r.status_code == 400
    assert "email" in r.json()["errors"]


@pytest.mark.skipif(connection.vendor == "sqlite", reason="needs real row locking")
@pytest.mark.django_db(transaction=True)
def test_concurrent_case_variant_emails_only_one_commits():
    a = User.objects.create_account("01011110000", PASSWORD)
    b = User.objects.create_account("01011110001", PASSWORD)
    results = []

    def go(u, email):
        try:
            User.objects.filter(pk=u.pk).update(email=email)
            results.append("ok")
        except IntegrityError:
            results.append("dup")
        finally:
            connection.close()

    ts = [
        threading.Thread(target=go, args=(a, "Z@x.com")),
        threading.Thread(target=go, args=(b, "z@X.com")),
    ]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert sorted(results) == ["dup", "ok"]
