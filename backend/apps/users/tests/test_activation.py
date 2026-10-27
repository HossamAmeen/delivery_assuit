import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from apps.users.models import AccountAction

from .conftest import PASSWORD, client_for, make_user

AR = {"HTTP_ACCEPT_LANGUAGE": "ar"}
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "activation-tests",
        }
    }
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


def act(c, user, name):
    return c.post(reverse(f"user-{name}", args=[user.pk]), {}, format="json")


def login(user, password=PASSWORD):
    return APIClient().post(
        reverse("token"),
        {"username_or_phone": user.username, "password": password},
        format="json",
    )


@pytest.mark.parametrize("role", ["driver", "trader", "client", "manager"])
def test_deactivate_then_activate_with_action_rows(admin_client, admin, role):
    u = make_user("target", role, "01077777777")
    r = act(admin_client, u, "deactivate")
    assert r.status_code == 200
    assert r.json()["message"] == "User deactivated."
    assert r.json()["data"]["user"]["status"] == "deactivated"
    assert r.json()["data"]["user"]["last_action"]["action"] == "deactivated"
    assert r.json()["data"]["user"]["last_action"]["actor_id"] == admin.pk
    r = act(admin_client, u, "activate")
    assert r.status_code == 200
    assert r.json()["message"] == "User activated."
    assert r.json()["data"]["user"]["status"] == "active"
    assert r.json()["data"]["user"]["last_action"]["action"] == "activated"
    assert list(
        AccountAction.objects.filter(user=u)
        .order_by("id")
        .values_list("action", flat=True)
    ) == ["deactivated", "activated"]


def test_deactivated_user_cannot_log_in_and_old_access_token_gets_403(admin_client):
    u = make_user("target", "client", "01077777777")
    target_client = client_for(u)
    assert target_client.get(reverse("me")).status_code == 200
    act(admin_client, u, "deactivate")
    r = target_client.get(reverse("me"))
    assert r.status_code == 403
    assert r.json()["code"] == "account_deactivated"
    r = login(u)
    assert r.status_code == 403
    assert r.json()["code"] == "account_deactivated"


def test_refresh_tokens_fail_after_deactivation_and_are_not_restored(admin_client):
    u = make_user("target", "driver", "01077777777")
    cookies = [login(u).cookies["delivery_refresh"].value for _ in range(2)]
    act(admin_client, u, "deactivate")
    assert BlacklistedToken.objects.filter(token__user=u).count() == 2

    def refresh(cookie):
        return APIClient().post(
            reverse("token-refresh"),
            {},
            format="json",
            HTTP_ORIGIN="http://localhost:5173",
            HTTP_COOKIE=f"delivery_refresh={cookie}",
        )

    assert all(refresh(c).status_code == 401 for c in cookies)
    act(admin_client, u, "activate")
    assert all(refresh(c).status_code == 401 for c in cookies)
    assert login(u).status_code == 200


def test_activated_user_logs_in_again(admin_client):
    u = make_user("target", "client", "01077777777", status="deactivated")
    assert login(u).status_code == 403
    act(admin_client, u, "activate")
    assert login(u).status_code == 200


@pytest.mark.parametrize("status", ["pending_approval", "rejected", "deactivated"])
def test_deactivate_only_from_active(admin_client, status):
    u = make_user("target", "driver", "01077777777", status=status)
    r = act(admin_client, u, "deactivate")
    assert r.status_code == 400
    assert r.json()["errors"] == {
        "status": ["Only an active account can be deactivated."]
    }
    u.refresh_from_db()
    assert u.status == status
    assert AccountAction.objects.count() == 0


@pytest.mark.parametrize("status", ["pending_approval", "rejected", "active"])
def test_activate_only_from_deactivated(admin_client, status):
    u = make_user("target", "trader", "01077777777", status=status)
    r = act(admin_client, u, "activate")
    assert r.status_code == 400
    assert r.json()["errors"] == {
        "status": ["Only a deactivated account can be activated."]
    }
    u.refresh_from_db()
    assert u.status == status
    assert AccountAction.objects.count() == 0


def test_cannot_deactivate_yourself(admin_client, admin, manager_client, manager):
    for c, me in ((admin_client, admin), (manager_client, manager)):
        r = act(c, me, "deactivate")
        assert r.status_code == 400
        assert r.json()["errors"] == {
            "non_field_errors": ["You cannot deactivate your own account."]
        }
        me.refresh_from_db()
        assert me.status == "active"


def test_admin_can_deactivate_another_admin(admin_client):
    other = make_user("admin2", "admin", "01000000099")
    assert act(admin_client, other, "deactivate").status_code == 200


def test_br14_manager_cannot_touch_admin_including_deactivated_one(
    manager_client, admin
):
    """BR-14: a Manager never manages an Admin account."""
    for status in ("active", "deactivated"):
        admin.status = status
        admin.save()
        for name in ("activate", "deactivate"):
            r = act(manager_client, admin, name)
            assert r.status_code == 403
            assert r.json()["code"] == "admin_protected"
    admin.refresh_from_db()
    assert admin.status == "deactivated"
    assert AccountAction.objects.count() == 0


def test_manager_can_deactivate_another_manager(manager_client):
    other = make_user("manager2", "manager", "01000000098")
    assert act(manager_client, other, "deactivate").status_code == 200


@pytest.mark.parametrize("role", ["driver", "trader", "client"])
def test_non_staff_always_403(role):
    caller = make_user("caller", role, "01088888888")
    victim = make_user("victim", "client", "01099999999")
    c = client_for(caller)
    assert act(c, victim, "deactivate").status_code == 403
    assert act(c, victim, "activate").status_code == 403
    victim.refresh_from_db()
    assert victim.status == "active"


def test_anonymous_401_and_unknown_404(admin_client):
    victim = make_user("victim", "client", "01099999999")
    assert act(APIClient(), victim, "deactivate").status_code == 401
    r = admin_client.post(reverse("user-deactivate", args=[99999]), {}, format="json")
    assert r.status_code == 404
    victim.soft_delete()
    assert act(admin_client, victim, "deactivate").status_code == 404


def test_deactivating_a_driver_changes_only_account_state(admin_client):
    """Orders do not exist yet; the rule for later is in the service docstring."""
    from apps.users import admin_services

    assert "assigned" in admin_services.deactivate_account.__doc__
    u = make_user("drv", "driver", "01012121212")
    act(admin_client, u, "deactivate")
    u.refresh_from_db()
    assert (u.role, u.deleted_at) == ("driver", None)


def test_messages_in_arabic(admin_client):
    u = make_user("target", "client", "01077777777")
    r = admin_client.post(
        reverse("user-deactivate", args=[u.pk]), {}, format="json", **AR
    )
    assert r.json()["message"] == "تم تعطيل المستخدم."
    r = admin_client.post(
        reverse("user-deactivate", args=[u.pk]), {}, format="json", **AR
    )
    assert r.json()["errors"]["status"] == ["يمكن تعطيل الحساب النشط فقط."]
    r = admin_client.post(
        reverse("user-activate", args=[u.pk]), {}, format="json", **AR
    )
    assert r.json()["message"] == "تم تفعيل المستخدم."
