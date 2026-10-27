import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from .conftest import client_for, make_order

pytestmark = pytest.mark.django_db
URL = "order-summary"


def summary(c):
    return c.get(reverse(URL)).json()["data"]


@pytest.fixture
def mix(client_user, shop, driver, admin):
    from apps.orders.models import OrderStatusChange

    out = {}
    for status in (
        "created",
        "available",
        "assigned",
        "picked_up",
        "in_delivery",
        "delivered",
        "cancelled",
    ):
        o = make_order(
            client_user,
            shop=shop,
            status=status,
            driver=driver
            if status in ("assigned", "picked_up", "in_delivery", "delivered")
            else None,
        )
        if status != "created" and status != "cancelled":
            OrderStatusChange.objects.create(
                order=o, from_status="created", to_status="available", actor=admin
            )
        out[status] = o
    return out


def test_anonymous_is_401():
    assert APIClient().get(reverse(URL)).status_code == 401


def test_staff_and_client_see_the_whole_mix(mix, admin, client_user):
    for user in (admin, client_user):
        assert summary(client_for(user)) == {
            "total": 7,
            "waiting_review": 1,
            "waiting_for_driver": 1,
            "in_progress": 3,
            "delivered": 1,
            "cancelled": 1,
        }


def test_trader_never_counts_unreviewed_orders(mix, trader):
    s = summary(client_for(trader))
    assert s["waiting_review"] == 0
    # created and the cancelled-before-review order are not theirs to see
    assert s["total"] == 5 and s["waiting_for_driver"] == 1 and s["in_progress"] == 3
    assert s["delivered"] == 1 and s["cancelled"] == 0


def test_driver_counts_only_their_own(mix, driver, driver2):
    assert summary(client_for(driver))["total"] == 4
    assert summary(client_for(driver2)) == {
        "total": 0,
        "waiting_review": 0,
        "waiting_for_driver": 0,
        "in_progress": 0,
        "delivered": 0,
        "cancelled": 0,
    }


def test_counts_add_up_and_match_the_list(mix, trader, client_user, admin, driver):
    for user in (trader, client_user, admin, driver):
        c = client_for(user)
        s = summary(c)
        parts = (
            s["waiting_review"]
            + s["waiting_for_driver"]
            + s["in_progress"]
            + s["delivered"]
            + s["cancelled"]
        )
        assert parts == s["total"]
        assert c.get(reverse("order-list")).json()["data"]["count"] == s["total"]
        assert (
            c.get(reverse("order-list"), {"status": "delivered"}).json()["data"][
                "count"
            ]
            == s["delivered"]
        )


def test_only_the_traders_own_shop(mix, trader2, client2, trader):
    other = make_order(
        client2,
        shop=trader2.shop if hasattr(trader2, "shop") else None,
        status="available",
    )
    assert other
    assert summary(client_for(trader))["total"] == 5
