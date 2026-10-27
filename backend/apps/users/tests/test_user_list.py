import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.models import AccountAction

from .conftest import client_for, make_user

pytestmark = pytest.mark.django_db
ROW_KEYS = {"id", "full_name", "phone", "username", "email", "role", "status"}


@pytest.fixture(autouse=True)
def isolated_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "user-list-tests",
        }
    }
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def people(admin, manager):
    return {
        "ahmed": make_user("ahmed", "driver", "01011110001", full_name="Ahmed Ali"),
        "sara": make_user(
            "sara",
            "trader",
            "01011110002",
            full_name="Sara Omar",
            status="pending_approval",
        ),
        "omar": make_user(
            "omar",
            "client",
            "01022220003",
            full_name="Omar Khaled",
            status="deactivated",
        ),
    }


def get(c, **params):
    return c.get(reverse("user-list"), params)


def test_admin_and_manager_get_paginated_list(admin_client, manager_client, people):
    for c in (admin_client, manager_client):
        r = get(c)
        assert r.status_code == 200
        data = r.json()["data"]
        assert r.json()["success"] is True
        assert data["count"] == 5
        assert {"next", "previous", "results"} <= set(data)
        assert all(set(row) == ROW_KEYS for row in data["results"])


def test_manager_list_includes_admin_rows(manager_client, admin):
    rows = get(manager_client).json()["data"]["results"]
    assert admin.pk in {r["id"] for r in rows}


def test_newest_first_and_soft_deleted_omitted(admin_client, people):
    people["omar"].soft_delete()
    ids = [r["id"] for r in get(admin_client).json()["data"]["results"]]
    assert ids == sorted(ids, reverse=True)
    assert people["omar"].pk not in ids


def test_pagination_defaults_and_limits(admin_client, admin):
    for i in range(25):
        make_user(f"u{i}", "client", f"0109{i:07d}")
    data = get(admin_client).json()["data"]
    assert data["count"] == 26
    assert len(data["results"]) == 20
    assert data["next"] is not None
    assert len(get(admin_client, page=2).json()["data"]["results"]) == 6
    assert len(get(admin_client, page_size=5).json()["data"]["results"]) == 5
    assert len(get(admin_client, page_size=1000).json()["data"]["results"]) == 26


def test_filters_by_role_and_status(admin_client, people):
    rows = get(admin_client, role="driver").json()["data"]["results"]
    assert {r["username"] for r in rows} == {"ahmed"}
    rows = get(admin_client, status="pending_approval").json()["data"]["results"]
    assert {r["username"] for r in rows} == {"sara"}
    rows = get(admin_client, role="client", status="deactivated").json()["data"][
        "results"
    ]
    assert {r["username"] for r in rows} == {"omar"}
    assert (
        get(admin_client, role="client", status="active").json()["data"]["count"] == 0
    )


def test_invalid_filter_values_are_400(admin_client):
    assert get(admin_client, role="king").status_code == 400
    assert get(admin_client, status="nope").status_code == 400


@pytest.mark.parametrize(
    "q,expected",
    [
        ("ahm", {"ahmed"}),
        ("SARA", {"sara"}),
        ("omar", {"sara", "omar"}),
        ("0101111", {"ahmed", "sara"}),
        ("0102 222", {"omar"}),
        ("nobody", set()),
    ],
)
def test_search_name_or_phone(admin_client, people, q, expected):
    rows = get(admin_client, search=q).json()["data"]["results"]
    assert {r["username"] for r in rows} == expected


def test_search_does_not_match_username_or_email(admin_client, people):
    people["ahmed"].email = "zzz@example.com"
    people["ahmed"].save()
    assert get(admin_client, search="zzz").json()["data"]["count"] == 0
    make_user("handle77", "client", "01033330077", full_name="Plain Person")
    assert get(admin_client, search="handle77").json()["data"]["count"] == 0
    assert get(admin_client, search="plain").json()["data"]["count"] == 1


@pytest.mark.parametrize("role", ["client", "driver", "trader"])
def test_other_roles_403_and_anonymous_401(role, people):
    caller = make_user("caller", role, "01099990000")
    c = client_for(caller)
    assert get(c).status_code == 403
    assert c.get(reverse("user-detail", args=[people["ahmed"].pk])).status_code == 403
    assert get(APIClient()).status_code == 401
    assert (
        APIClient().get(reverse("user-detail", args=[people["ahmed"].pk])).status_code
        == 401
    )


def test_detail_shows_profile_and_last_action(admin_client, admin, people):
    AccountAction.objects.create(
        user=people["sara"], actor=admin, action="rejected", reason="Bad photo"
    )
    AccountAction.objects.create(user=people["sara"], actor=admin, action="approved")
    r = admin_client.get(reverse("user-detail", args=[people["sara"].pk]))
    assert r.status_code == 200
    u = r.json()["data"]["user"]
    assert u["username"] == "sara"
    assert u["last_action"]["action"] == "approved"
    assert u["last_action"]["actor_name"] == admin.full_name
    assert set(u) == ROW_KEYS | {"rejection_reason", "last_action"}


def test_detail_last_action_null_and_manager_may_read_admin(
    admin_client, manager_client, admin
):
    r = manager_client.get(reverse("user-detail", args=[admin.pk]))
    assert r.status_code == 200
    assert r.json()["data"]["user"]["last_action"] is None
    assert r.json()["data"]["user"]["role"] == "admin"


def test_detail_hides_secrets(admin_client, people):
    body = admin_client.get(reverse("user-detail", args=[people["ahmed"].pk])).content
    for word in (b"password", b"is_staff", b"is_superuser", b"pbkdf2"):
        assert word not in body
    body = get(admin_client).content
    for word in (b"password", b"is_staff", b"is_superuser", b"pbkdf2"):
        assert word not in body


def test_detail_404_for_unknown_and_deleted(admin_client, people):
    assert admin_client.get(reverse("user-detail", args=[99999])).status_code == 404
    people["ahmed"].soft_delete()
    assert (
        admin_client.get(reverse("user-detail", args=[people["ahmed"].pk])).status_code
        == 404
    )


def test_list_query_count_does_not_grow_with_rows(admin_client, admin):
    with CaptureQueriesContext(connection) as few:
        get(admin_client)
    for i in range(15):
        make_user(f"bulk{i}", "client", f"0108{i:07d}")
    with CaptureQueriesContext(connection) as many:
        get(admin_client)
    assert len(many) == len(few)
