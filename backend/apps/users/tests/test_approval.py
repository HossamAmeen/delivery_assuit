import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.users import admin_services
from apps.users.models import AccountAction, User

from .conftest import PASSWORD, client_for, make_user

AR = {"HTTP_ACCEPT_LANGUAGE": "ar"}
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "approval-tests",
        }
    }
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def pending_driver():
    return make_user("pd", "driver", "01011111111", status="pending_approval")


@pytest.fixture
def pending_trader():
    return make_user("pt", "trader", "01022222222", status="pending_approval")


def approve(c, user):
    return c.post(reverse("user-approve", args=[user.pk]), {}, format="json")


def reject(c, user, **body):
    return c.post(reverse("user-reject", args=[user.pk]), body, format="json")


def login(username, password=PASSWORD):
    return APIClient().post(
        reverse("token"),
        {"username_or_phone": username, "password": password},
        format="json",
    )


@pytest.mark.parametrize("who", ["pending_driver", "pending_trader"])
@pytest.mark.parametrize("staff", ["admin_client", "manager_client"])
def test_approve_sets_active_and_records_who_and_when(
    who, staff, request, admin, manager
):
    target = request.getfixturevalue(who)
    c = request.getfixturevalue(staff)
    r = approve(c, target)
    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "User approved."
    u = body["data"]["user"]
    assert u["status"] == "active"
    assert u["rejection_reason"] == ""
    assert u["last_action"]["action"] == "approved"
    actor = admin if staff == "admin_client" else manager
    assert u["last_action"]["actor_id"] == actor.pk
    assert u["last_action"]["actor_name"] == actor.full_name
    assert u["last_action"]["created_at"].endswith("Z")
    target.refresh_from_db()
    assert target.status == "active"
    assert login(target.username).status_code == 200
    assert AccountAction.objects.filter(user=target).count() == 1


def test_reject_with_reason(admin_client, admin, pending_driver):
    r = reject(admin_client, pending_driver, reason="  Missing documents  ")
    assert r.status_code == 200
    u = r.json()["data"]["user"]
    assert r.json()["message"] == "User rejected."
    assert u["status"] == "rejected"
    assert u["rejection_reason"] == "Missing documents"
    assert u["last_action"]["action"] == "rejected"
    assert u["last_action"]["reason"] == "Missing documents"
    pending_driver.refresh_from_db()
    assert pending_driver.status == "rejected"


@pytest.mark.parametrize("body", [{}, {"reason": ""}])
def test_reject_without_reason(admin_client, pending_trader, body):
    r = reject(admin_client, pending_trader, **body)
    assert r.status_code == 200
    assert r.json()["data"]["user"]["rejection_reason"] == ""


def test_reason_too_long_is_400_and_unchanged(admin_client, pending_driver):
    r = reject(admin_client, pending_driver, reason="x" * 501)
    assert r.status_code == 400
    assert "reason" in r.json()["errors"]
    pending_driver.refresh_from_db()
    assert pending_driver.status == "pending_approval"
    assert AccountAction.objects.count() == 0


def test_rejected_user_with_right_password_gets_403_account_rejected(
    admin_client, pending_driver
):
    reject(admin_client, pending_driver, reason="Bad photo")
    r = login("pd")
    assert r.status_code == 403
    assert r.json() == {
        "success": False,
        "message": "Your registration was rejected. Reason: Bad photo.",
        "errors": {},
        "code": "account_rejected",
    }
    assert "access" not in r.content.decode()
    assert "delivery_refresh" not in r.cookies


def test_rejected_without_reason_message(pending_driver):
    pending_driver.status = "rejected"
    pending_driver.save()
    assert login("pd").json()["message"] == "Your registration was rejected."


def test_rejected_with_wrong_password_is_generic_401(pending_driver):
    pending_driver.status = "rejected"
    pending_driver.save()
    r = login("pd", "wrong-pass")
    assert r.status_code == 401
    assert r.json()["message"] == "Invalid credentials."
    assert "code" not in r.json()


def test_rejected_message_in_arabic(pending_driver):
    pending_driver.status = "rejected"
    pending_driver.rejection_reason = "صورة غير واضحة"
    pending_driver.save()
    r = APIClient().post(
        reverse("token"),
        {"username_or_phone": "pd", "password": PASSWORD},
        format="json",
        **AR,
    )
    assert r.json()["message"] == "تم رفض تسجيلك. السبب: صورة غير واضحة."


def test_rejected_cannot_refresh(pending_driver):
    c = APIClient()
    pending_driver.status = "active"
    pending_driver.save()
    r = c.post(
        reverse("token"),
        {"username_or_phone": "pd", "password": PASSWORD},
        format="json",
    )
    cookie = r.cookies["delivery_refresh"].value
    pending_driver.status = "rejected"
    pending_driver.save()
    r = APIClient().post(
        reverse("token-refresh"),
        {},
        format="json",
        HTTP_ORIGIN="http://localhost:5173",
        HTTP_COOKIE=f"delivery_refresh={cookie}",
    )
    assert r.status_code == 401


def test_approve_clears_old_reason_after_status_reset(admin_client, pending_driver):
    pending_driver.rejection_reason = "old"
    pending_driver.save()
    r = approve(admin_client, pending_driver)
    assert r.json()["data"]["user"]["rejection_reason"] == ""


@pytest.mark.parametrize("status", ["active", "deactivated", "rejected"])
def test_approve_and_reject_only_from_pending(admin_client, status):
    u = make_user("u1", "driver", "01033333333", status=status)
    for call in (approve, reject):
        r = call(admin_client, u)
        assert r.status_code == 400
        assert list(r.json()["errors"]) == ["status"]
    u.refresh_from_db()
    assert u.status == status
    assert AccountAction.objects.count() == 0


def test_error_messages_are_exact(admin_client):
    u = make_user("u2", "driver", "01044444444")
    assert approve(admin_client, u).json()["errors"]["status"] == [
        "Only a pending driver or trader can be approved."
    ]
    assert reject(admin_client, u).json()["errors"]["status"] == [
        "Only a pending driver or trader can be rejected."
    ]


@pytest.mark.parametrize("role", ["client", "manager", "admin"])
def test_other_roles_cannot_be_approved_even_if_pending(admin_client, role):
    u = make_user("u3", role, "01055555555", status="pending_approval")
    assert approve(admin_client, u).status_code == 400
    assert reject(admin_client, u).status_code == 400
    u.refresh_from_db()
    assert u.status == "pending_approval"
    assert AccountAction.objects.count() == 0


@pytest.mark.parametrize("role", ["client", "driver", "trader"])
def test_non_staff_callers_get_403(role, pending_driver):
    caller = make_user("caller", role, "01066666666")
    c = client_for(caller)
    assert approve(c, pending_driver).status_code == 403
    assert reject(c, pending_driver).status_code == 403
    pending_driver.refresh_from_db()
    assert pending_driver.status == "pending_approval"


def test_anonymous_401(pending_driver):
    c = APIClient()
    assert approve(c, pending_driver).status_code == 401
    assert reject(c, pending_driver).status_code == 401


def test_manager_cannot_act_on_admin_even_though_none_is_pending(manager_client, admin):
    admin.status = "pending_approval"
    admin.save()
    for call in (approve, reject):
        r = call(manager_client, admin)
        assert r.status_code == 403
        assert r.json()["code"] == "admin_protected"
        assert r.json()["message"] == "You cannot manage an administrator account."
    assert AccountAction.objects.count() == 0


def test_unknown_and_deleted_targets_are_404(admin_client, pending_driver):
    r = admin_client.post(reverse("user-approve", args=[99999]), {}, format="json")
    assert r.status_code == 404
    pending_driver.soft_delete()
    pending_driver.save()
    assert approve(admin_client, pending_driver).status_code == 404


def test_approving_twice_second_is_400_and_one_row(admin_client, pending_driver):
    assert approve(admin_client, pending_driver).status_code == 200
    assert approve(admin_client, pending_driver).status_code == 400
    assert AccountAction.objects.count() == 1


def test_response_hides_secrets(admin_client, pending_driver):
    u = approve(admin_client, pending_driver).json()["data"]["user"]
    assert set(u) == {
        "id",
        "full_name",
        "phone",
        "username",
        "email",
        "role",
        "status",
        "rejection_reason",
        "last_action",
    }


def test_me_includes_rejection_reason(admin_client):
    u = admin_client.get(reverse("me")).json()["data"]["user"]
    assert u["rejection_reason"] == ""


def test_messages_in_arabic(admin_client, pending_driver):
    r = admin_client.post(
        reverse("user-approve", args=[pending_driver.pk]), {}, format="json", **AR
    )
    assert r.json()["message"] == "تم قبول المستخدم."
    r = admin_client.post(
        reverse("user-approve", args=[pending_driver.pk]), {}, format="json", **AR
    )
    assert r.json()["errors"]["status"] == [
        "يمكن قبول المندوب أو التاجر قيد الانتظار فقط."
    ]


def test_is_publicly_operable_helper():
    """Orders and shops (later sprints) must call this (BR-5, BR-15)."""
    cases = {
        "active": True,
        "pending_approval": False,
        "rejected": False,
        "deactivated": False,
    }
    for status, expected in cases.items():
        u = User(role="driver", status=status)
        assert admin_services.is_publicly_operable(u) is expected
    gone = User(role="trader", status="active", deleted_at=timezone.now())
    assert admin_services.is_publicly_operable(gone) is False
