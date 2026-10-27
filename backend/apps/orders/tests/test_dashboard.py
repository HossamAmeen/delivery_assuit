import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.orders.models import Order

from .conftest import client_for, make_order, make_user

pytestmark = pytest.mark.django_db
URL = "staff-dashboard"


def get(c, **params):
    return c.get(reverse(URL), params)


def age(order, days):
    Order.objects.filter(pk=order.pk).update(
        created_at=timezone.now() - datetime.timedelta(days=days)
    )


@pytest.fixture
def world(client_user, client2, driver, trader):
    make_user("d_p", "driver", "01099990101", status="pending_approval")
    make_user("d_d", "driver", "01099990102", status="deactivated")
    make_user("d_r", "driver", "01099990103", status="rejected")
    make_user("t_p", "trader", "01099990201", status="pending_approval")
    orders = {}
    for key, status, days in (
        ("today_created", "created", 0),
        ("today_available", "available", 0),
        ("week_assigned", "assigned", 3),
        ("week_delivered", "delivered", 5),
        ("old_delivered", "delivered", 40),
        ("old_cancelled", "cancelled", 400),
        ("old_in_delivery", "in_delivery", 20),
        ("old_picked", "picked_up", 100),
    ):
        o = make_order(
            client_user,
            status=status,
            driver=driver
            if status in ("assigned", "picked_up", "in_delivery", "delivered")
            else None,
        )
        age(o, days)
        orders[key] = o
    return orders


class TestAccess:
    @pytest.mark.parametrize("role", ["client", "trader", "driver"])
    def test_staff_only(self, role):
        assert (
            get(client_for(make_user(f"u_{role}", role, "01099990009"))).status_code
            == 403
        )

    def test_anonymous_is_401(self):
        from rest_framework.test import APIClient

        assert APIClient().get(reverse(URL)).status_code == 401


class TestCounts:
    def test_accounts_by_status(self, world, admin):
        data = get(client_for(admin)).json()["data"]
        assert data["drivers"] == {
            "total": 4,
            "active": 1,
            "inactive": 1,
            "pending": 1,
            "rejected": 1,
        }
        assert data["traders"] == {
            "total": 2,
            "active": 1,
            "inactive": 0,
            "pending": 1,
            "rejected": 0,
        }
        assert data["clients"]["total"] == 2
        assert data["period"] == "all"

    def test_orders_all_time_use_the_documented_mapping(self, world, manager):
        o = get(client_for(manager)).json()["data"]["orders"]
        assert o == {
            "total": 8,
            "pending": 2,
            "in_progress": 3,
            "delivered": 2,
            "cancelled": 1,
        }
        assert (
            o["pending"] + o["in_progress"] + o["delivered"] + o["cancelled"]
            == o["total"]
        )

    def test_today_week_month(self, world, admin):
        c = client_for(admin)
        assert get(c, period="today").json()["data"]["orders"]["total"] == 2
        week = get(c, period="week").json()["data"]["orders"]
        assert week == {
            "total": 4,
            "pending": 2,
            "in_progress": 1,
            "delivered": 1,
            "cancelled": 0,
        }
        month = get(c, period="month").json()["data"]["orders"]["total"]
        assert 2 <= month <= 8

    def test_custom_range_is_inclusive(self, world, admin):
        today = timezone.localdate()
        start = (today - datetime.timedelta(days=5)).isoformat()
        end = (today - datetime.timedelta(days=3)).isoformat()
        o = get(
            client_for(admin), period="custom", **{"from": start, "to": end}
        ).json()["data"]["orders"]
        assert o["total"] == 2 and o["in_progress"] == 1 and o["delivered"] == 1

    def test_accounts_are_not_filtered_by_period(self, world, admin):
        data = get(client_for(admin), period="today").json()["data"]
        assert data["drivers"]["total"] == 4

    @pytest.mark.parametrize(
        "params",
        [
            {"period": "year"},
            {"period": "custom"},
            {"period": "custom", "from": "2026-10-10"},
            {"period": "custom", "from": "bad", "to": "2026-10-10"},
            {"period": "custom", "from": "2026-10-10", "to": "2026-10-01"},
        ],
    )
    def test_bad_periods_are_400(self, admin, params):
        assert get(client_for(admin), **params).status_code == 400

    def test_deleted_accounts_are_not_counted(self, world, admin, driver):
        driver.soft_delete()
        assert get(client_for(admin)).json()["data"]["drivers"]["total"] == 3

    def test_empty_system(self, admin):
        data = get(client_for(admin)).json()["data"]
        assert data["orders"]["total"] == 0 and data["drivers"]["total"] == 0
