import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from apps.users.models import User

from .conftest import PASSWORD, client_for, make_user

AR = {"HTTP_ACCEPT_LANGUAGE": "ar"}
NEW_PASSWORD = "Nw7#pQr!vB52xY"
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "user-write-tests",
        }
    }
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


def body(**over):
    data = {
        "full_name": "Sara Nabil",
        "phone": "0100 999 8877",
        "username": "sara",
        "email": "Sara@Example.com",
        "password": "S0me-Strong-Pass!9",
        "role": "manager",
    }
    data.update(over)
    return {k: v for k, v in data.items() if v is not None}


def create(c, **over):
    return c.post(reverse("user-list"), body(**over), format="json")


def patch(c, user, data, **extra):
    return c.patch(reverse("user-detail", args=[user.pk]), data, format="json", **extra)


def delete(c, user):
    return c.delete(reverse("user-detail", args=[user.pk]))


def login(ident, password):
    return APIClient().post(
        reverse("token"),
        {"username_or_phone": ident, "password": password},
        format="json",
    )


# --- create ------------------------------------------------------------------


@pytest.mark.parametrize("role", ["admin", "manager", "driver", "trader", "client"])
def test_admin_creates_any_role_active_and_can_log_in(admin_client, role):
    r = create(admin_client, role=role)
    assert r.status_code == 201, r.content
    u = r.json()["data"]["user"]
    assert r.json()["message"] == "User created."
    assert (u["role"], u["status"], u["last_action"]) == (role, "active", None)
    assert u["phone"] == "01009998877"
    assert u["email"] == "sara@example.com"
    assert login("sara", "S0me-Strong-Pass!9").status_code == 200
    row = User.objects.get(pk=u["id"])
    assert row.is_staff is (role == "admin")
    assert row.is_superuser is (role == "admin")


@pytest.mark.parametrize("role", ["manager", "driver", "trader", "client"])
def test_manager_creates_manager_and_other_roles(manager_client, role):
    assert create(manager_client, role=role).status_code == 201


def test_br14_manager_cannot_create_admin(manager_client):
    """BR-14: Manager cannot create, edit, or delete Admin accounts."""
    before = User.objects.count()
    r = create(manager_client, role="admin")
    assert r.status_code == 403
    assert r.json() == {
        "success": False,
        "message": "You cannot manage an administrator account.",
        "errors": {},
        "code": "admin_protected",
    }
    assert User.objects.count() == before


def test_manager_admin_role_is_403_even_when_body_is_invalid(manager_client):
    r = create(manager_client, role="admin", phone="1", password="1")
    assert r.status_code == 403


@pytest.mark.parametrize("role", ["driver", "trader", "client"])
def test_driver_username_optional(admin_client, role):
    r = create(admin_client, role=role, username=None)
    assert r.status_code == 201
    assert r.json()["data"]["user"]["username"] is None


@pytest.mark.parametrize("role", ["admin", "manager"])
def test_username_required_for_staff_roles(admin_client, role):
    r = create(admin_client, role=role, username=None)
    assert r.status_code == 400
    assert "username" in r.json()["errors"]
    assert create(admin_client, role=role, username="").status_code == 400


@pytest.mark.parametrize(
    "over,field",
    [
        ({"full_name": "A"}, "full_name"),
        ({"phone": "123"}, "phone"),
        ({"email": "nope"}, "email"),
        ({"password": "123"}, "password"),
        ({"password": "x" * 129}, "password"),
        ({"role": "boss"}, "role"),
        ({"role": None}, "role"),
        ({"password": None}, "password"),
        ({"phone": None}, "phone"),
        ({"full_name": None}, "full_name"),
    ],
)
def test_create_validation(admin_client, over, field):
    before = User.objects.count()
    r = create(admin_client, **over)
    assert r.status_code == 400
    assert field in r.json()["errors"]
    assert User.objects.count() == before


def test_create_duplicates(admin_client):
    make_user("taken", "client", "01011112222", email="t@example.com")
    r = create(
        admin_client, phone="0101-111-2222", email="T@example.com", username="taken"
    )
    assert r.status_code == 400
    assert r.json()["errors"] == {
        "phone": ["A user with this phone number already exists."],
        "email": ["A user with this email already exists."],
        "username": ["A user with this username already exists."],
    }


@pytest.mark.parametrize("key", ["status", "is_staff", "is_superuser"])
def test_create_refuses_status_and_staff_flags(admin_client, key):
    before = User.objects.count()
    r = create(admin_client, **{key: "active" if key == "status" else True})
    assert r.status_code == 400
    assert r.json()["errors"][key] == ["You cannot change this field."]
    assert User.objects.count() == before


@pytest.mark.parametrize("role", ["client", "driver", "trader"])
def test_non_staff_cannot_create(role):
    c = client_for(make_user("caller", role, "01099990000"))
    assert create(c, role="client").status_code == 403
    assert create(APIClient()).status_code == 401


# --- edit --------------------------------------------------------------------


def test_admin_edits_admin_and_manager(admin_client):
    other_admin = make_user("admin2", "admin", "01000000050")
    mgr = make_user("mgr2", "manager", "01000000051")
    for u in (other_admin, mgr):
        r = patch(admin_client, u, {"full_name": "Renamed Person", "email": "X@y.com"})
        assert r.status_code == 200, r.content
        assert r.json()["message"] == "User updated."
        assert r.json()["data"]["user"]["full_name"] == "Renamed Person"
        assert r.json()["data"]["user"]["email"] == "x@y.com"
        patch(admin_client, u, {"email": ""})


@pytest.mark.parametrize("role", ["manager", "driver", "trader", "client"])
def test_manager_edits_manager_and_others(manager_client, role):
    u = make_user("target", role, "01077770000")
    r = patch(manager_client, u, {"full_name": "New Name", "phone": "0100 111 2222"})
    assert r.status_code == 200
    u.refresh_from_db()
    assert (u.full_name, u.phone) == ("New Name", "01001112222")


def test_br14_manager_cannot_edit_admin_any_field(manager_client, admin):
    for data in (
        {"full_name": "Hacked Name"},
        {"password": NEW_PASSWORD},
        {"role": "client"},
        {},
    ):
        r = patch(manager_client, admin, data)
        assert r.status_code == 403
        assert r.json()["code"] == "admin_protected"
    admin.refresh_from_db()
    assert admin.full_name != "Hacked Name"
    assert admin.check_password(PASSWORD)
    assert admin.role == "admin"


def test_manager_cannot_promote_to_admin(manager_client):
    u = make_user("target", "client", "01077770000")
    r = patch(manager_client, u, {"role": "admin"})
    assert r.status_code == 403
    u.refresh_from_db()
    assert u.role == "client"
    assert not u.is_staff


def test_admin_changes_role_and_staff_flags_follow(admin_client):
    u = make_user("target", "client", "01077770000")
    assert (
        patch(admin_client, u, {"role": "admin", "username": "target"}).status_code
        == 200
    )
    u.refresh_from_db()
    assert (u.role, u.is_staff, u.is_superuser) == ("admin", True, True)
    assert patch(admin_client, u, {"role": "driver"}).status_code == 200
    u.refresh_from_db()
    assert (u.role, u.is_staff, u.is_superuser) == ("driver", False, False)


def test_cannot_change_own_role(admin_client, admin):
    r = patch(admin_client, admin, {"role": "manager"})
    assert r.status_code == 400
    assert r.json()["errors"] == {"role": ["You cannot change your own role."]}
    assert patch(admin_client, admin, {"role": "admin"}).status_code == 200


@pytest.mark.parametrize("key", ["status", "is_staff", "is_superuser"])
def test_patch_refuses_status_and_flags_and_saves_nothing(admin_client, key):
    u = make_user("target", "client", "01077770000")
    r = patch(
        admin_client,
        u,
        {"full_name": "Changed Name", key: "active" if key == "status" else True},
    )
    assert r.status_code == 400
    assert r.json()["errors"][key] == ["You cannot change this field."]
    u.refresh_from_db()
    assert u.full_name != "Changed Name"


def test_patch_password_sets_it_and_revokes_refresh_tokens(admin_client):
    u = make_user("target", "driver", "01077770000")
    login("target", PASSWORD)
    login("target", PASSWORD)
    r = patch(admin_client, u, {"password": NEW_PASSWORD})
    assert r.status_code == 200
    assert NEW_PASSWORD not in r.content.decode()
    assert BlacklistedToken.objects.filter(token__user=u).count() == 2
    assert login("target", NEW_PASSWORD).status_code == 200
    assert login("target", PASSWORD).status_code == 401


def test_patch_without_password_keeps_password_and_tokens(admin_client):
    u = make_user("target", "driver", "01077770000")
    login("target", PASSWORD)
    patch(admin_client, u, {"full_name": "Other Name"})
    assert BlacklistedToken.objects.count() == 0
    assert login("target", PASSWORD).status_code == 200


@pytest.mark.parametrize("pw", ["", "123", "x" * 129])
def test_patch_bad_password_400(admin_client, pw):
    u = make_user("target", "driver", "01077770000")
    r = patch(admin_client, u, {"password": pw})
    assert r.status_code == 400
    assert "password" in r.json()["errors"]
    u.refresh_from_db()
    assert u.check_password(PASSWORD)


def test_patch_duplicates_exclude_self(admin_client):
    make_user("other", "client", "01011112222", email="o@example.com")
    u = make_user("target", "client", "01077770000", email="t@example.com")
    r = patch(
        admin_client,
        u,
        {"phone": "01011112222", "email": "O@example.com", "username": "other"},
    )
    assert set(r.json()["errors"]) == {"phone", "email", "username"}
    assert (
        patch(
            admin_client,
            u,
            {"phone": "0107 777 0000", "email": "T@example.com", "username": "target"},
        ).status_code
        == 200
    )


def test_patch_blank_username_clears_for_driver_but_not_for_manager(admin_client):
    d = make_user("drv", "driver", "01077770001")
    assert (
        patch(admin_client, d, {"username": ""}).json()["data"]["user"]["username"]
        is None
    )
    m = make_user("mgr", "manager", "01077770002")
    r = patch(admin_client, m, {"username": ""})
    assert r.status_code == 400
    assert "username" in r.json()["errors"]
    r = patch(admin_client, d, {"role": "manager"})
    assert r.status_code == 400


def test_patch_404_and_non_staff(admin_client):
    ghost = User(pk=99999)
    assert patch(admin_client, ghost, {}).status_code == 404
    victim = make_user("victim", "client", "01088880000")
    for role in ("client", "driver", "trader"):
        c = client_for(
            make_user(f"c{role}", role, f"0109{role.__hash__() % 10**7:07d}")
        )
        assert patch(c, victim, {"full_name": "Nope Nope"}).status_code == 403
    assert patch(APIClient(), victim, {}).status_code == 401


def test_staff_can_edit_pending_user_without_changing_status(admin_client):
    u = make_user("pend", "driver", "01077770003", status="pending_approval")
    assert patch(admin_client, u, {"full_name": "Pending Person"}).status_code == 200
    u.refresh_from_db()
    assert u.status == "pending_approval"


# --- delete ------------------------------------------------------------------


@pytest.mark.parametrize("role", ["admin", "manager", "driver", "trader", "client"])
def test_admin_deletes_anyone(admin_client, role):
    u = make_user("target", role, "01077770000")
    login("target", PASSWORD)
    r = delete(admin_client, u)
    assert r.status_code == 200
    assert r.json() == {"success": True, "message": "User deleted.", "data": {}}
    assert User.objects.filter(pk=u.pk).count() == 0
    assert User.all_objects.get(pk=u.pk).deleted_at is not None
    assert login("target", PASSWORD).status_code == 401
    assert BlacklistedToken.objects.filter(token__user=u).count() == 1


@pytest.mark.parametrize("role", ["manager", "driver", "trader", "client"])
def test_manager_deletes_manager_and_others(manager_client, role):
    u = make_user("target", role, "01077770000")
    assert delete(manager_client, u).status_code == 200


def test_br14_manager_cannot_delete_admin(manager_client, admin):
    r = delete(manager_client, admin)
    assert r.status_code == 403
    assert r.json()["code"] == "admin_protected"
    assert User.objects.filter(pk=admin.pk).exists()


def test_cannot_delete_yourself(admin_client, admin, manager_client, manager):
    for c, me in ((admin_client, admin), (manager_client, manager)):
        r = delete(c, me)
        assert r.status_code == 400
        assert r.json()["errors"] == {
            "non_field_errors": ["You cannot delete your own account."]
        }
        assert User.objects.filter(pk=me.pk).exists()


def test_deleted_user_old_access_token_stops_working(admin_client):
    u = make_user("target", "client", "01077770000")
    c = client_for(u)
    assert c.get(reverse("me")).status_code == 200
    delete(admin_client, u)
    assert c.get(reverse("me")).status_code == 401


def test_deleted_twice_is_404_and_phone_stays_reserved(admin_client):
    u = make_user("target", "client", "01077770000")
    delete(admin_client, u)
    assert delete(admin_client, u).status_code == 404
    r = create(admin_client, phone="01077770000", username="fresh")
    assert r.status_code == 400
    assert "phone" in r.json()["errors"]


@pytest.mark.parametrize("role", ["client", "driver", "trader"])
def test_non_staff_cannot_delete(role):
    victim = make_user("victim", "client", "01088880000")
    c = client_for(make_user("caller", role, "01099990000"))
    assert delete(c, victim).status_code == 403
    assert delete(APIClient(), victim).status_code == 401


def test_messages_in_arabic(admin_client):
    r = admin_client.post(
        reverse("user-list"), body(role="driver"), format="json", **AR
    )
    assert r.json()["message"] == "تم إنشاء المستخدم."
    u = User.objects.get(username="sara")
    r = admin_client.patch(
        reverse("user-detail", args=[u.pk]),
        {"full_name": "Sara N"},
        format="json",
        **AR,
    )
    assert r.json()["message"] == "تم تحديث المستخدم."
    r = admin_client.delete(reverse("user-detail", args=[u.pk]), **AR)
    assert r.json()["message"] == "تم حذف المستخدم."
