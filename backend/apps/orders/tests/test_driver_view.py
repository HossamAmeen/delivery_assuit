import pytest
from django.urls import reverse

from apps.orders import lifecycle
from apps.orders.models import OrderStatusChange

from .conftest import client_for, make_order

pytestmark = pytest.mark.django_db
LIST = "order-list"


def detail(pk):
    return reverse("order-detail", args=[pk])


def ids(r):
    return [o["id"] for o in r.json()["data"]["results"]]


@pytest.fixture
def jobs(client_user, shop, driver, admin):
    """One order per status for the driver, assigned in a known sequence."""
    out = {}
    for status in ("assigned", "picked_up", "in_delivery", "delivered", "cancelled"):
        o = make_order(client_user, shop=shop, status=status, driver=driver)
        # a real job went through review and assignment
        OrderStatusChange.objects.create(
            order=o, from_status="created", to_status="available", actor=admin
        )
        OrderStatusChange.objects.create(
            order=o, from_status="available", to_status="assigned", actor=admin
        )
        if status == "delivered":
            OrderStatusChange.objects.create(
                order=o, from_status="in_delivery", to_status="delivered", actor=driver
            )
        out[status] = o
    return out


class TestScopes:
    def test_active_lists_the_three_execution_statuses_newest_assignment_first(
        self, jobs, driver
    ):
        r = client_for(driver).get(reverse(LIST), {"scope": "active"})
        assert ids(r) == [
            jobs["in_delivery"].pk,
            jobs["picked_up"].pk,
            jobs["assigned"].pk,
        ]

    def test_history_lists_delivered_and_cancelled_newest_first(self, jobs, driver):
        r = client_for(driver).get(reverse(LIST), {"scope": "history"})
        assert ids(r) == [jobs["cancelled"].pk, jobs["delivered"].pk]

    def test_unknown_scope_is_400(self, driver):
        assert (
            client_for(driver).get(reverse(LIST), {"scope": "all"}).status_code == 400
        )

    def test_scope_combines_with_status(self, jobs, driver):
        r = client_for(driver).get(
            reverse(LIST), {"scope": "active", "status": "picked_up"}
        )
        assert ids(r) == [jobs["picked_up"].pk]

    def test_scope_never_reveals_other_drivers_orders(self, jobs, driver2):
        c = client_for(driver2)
        for scope in ("active", "history"):
            assert ids(c.get(reverse(LIST), {"scope": scope})) == []

    def test_history_is_paginated(self, client_user, driver):
        for _ in range(3):
            make_order(client_user, status="delivered", driver=driver)
        data = (
            client_for(driver)
            .get(reverse(LIST), {"scope": "history", "page_size": 2})
            .json()["data"]
        )
        assert data["count"] == 3 and len(data["results"]) == 2 and data["next"]

    def test_staff_can_use_scopes_too(self, jobs, admin):
        r = client_for(admin).get(reverse(LIST), {"scope": "history"})
        assert set(ids(r)) == {jobs["delivered"].pk, jobs["cancelled"].pk}

    def test_cancelled_by_staff_leaves_active_and_frees_the_driver(
        self, jobs, driver, admin
    ):
        from apps.orders import assign

        lifecycle.transition(jobs["assigned"], "cancelled", admin, reason="stop")
        c = client_for(driver)
        assert jobs["assigned"].pk not in ids(c.get(reverse(LIST), {"scope": "active"}))
        assert jobs["assigned"].pk in ids(c.get(reverse(LIST), {"scope": "history"}))
        jobs["picked_up"].status = "delivered"
        jobs["picked_up"].save()
        jobs["in_delivery"].status = "delivered"
        jobs["in_delivery"].save()
        assert not assign.has_active_order(driver)


class TestFields:
    def test_times_and_next_action_for_the_assigned_driver(self, jobs, driver):
        c = client_for(driver)
        a = c.get(detail(jobs["assigned"].pk)).json()["data"]["order"]
        assert a["assigned_at"] and a["delivered_at"] is None
        assert a["next_action"] == "pick_up"
        d = c.get(detail(jobs["delivered"].pk)).json()["data"]["order"]
        assert d["delivered_at"] and d["next_action"] is None
        assert (
            c.get(detail(jobs["picked_up"].pk)).json()["data"]["order"]["next_action"]
            == "start_delivery"
        )
        assert (
            c.get(detail(jobs["in_delivery"].pk)).json()["data"]["order"]["next_action"]
            == "deliver"
        )

    def test_no_next_action_for_anyone_else(self, jobs, admin, client_user):
        for user in (admin, client_user):
            o = (
                client_for(user)
                .get(detail(jobs["assigned"].pk))
                .json()["data"]["order"]
            )
            assert o["next_action"] is None

    def test_unassigned_order_has_null_times(self, order, client_user):
        o = client_for(client_user).get(detail(order.pk)).json()["data"]["order"]
        assert o["assigned_at"] is None and o["delivered_at"] is None


class TestContactNumbers:
    """BR-16: the dedicated permission test."""

    def test_assigned_driver_sees_client_and_shop_phones_while_active(
        self, jobs, driver, client_user, trader
    ):
        trader.shop.phone = "01005550000"
        trader.shop.save()
        c = client_for(driver)
        for status in ("assigned", "picked_up", "in_delivery"):
            o = c.get(detail(jobs[status].pk)).json()["data"]["order"]
            assert o["client"]["phone"] == client_user.phone, status
            assert o["shop"]["phone"] == "01005550000", status

    def test_phones_disappear_once_delivered_or_cancelled(self, jobs, driver):
        c = client_for(driver)
        for status in ("delivered", "cancelled"):
            o = c.get(detail(jobs[status].pk)).json()["data"]["order"]
            assert "phone" not in o["client"], status
            assert "phone" not in o["shop"], status

    def test_an_unassigned_driver_cannot_even_open_the_order(self, jobs, driver2):
        assert client_for(driver2).get(detail(jobs["assigned"].pk)).status_code == 404

    def test_client_never_sees_the_shop_or_driver_phone_and_trader_never_the_client_phone(
        self, jobs, client_user, trader, admin, driver
    ):
        trader.shop.phone = "01005550000"
        trader.shop.save()
        lifecycle_ok = jobs["assigned"]
        mine = (
            client_for(client_user).get(detail(lifecycle_ok.pk)).json()["data"]["order"]
        )
        assert "phone" not in mine["shop"] and "phone" not in mine["client"]
        assert "phone" not in mine["driver"]
        shop_side = client_for(trader).get(detail(lifecycle_ok.pk))
        assert shop_side.status_code == 200
        body = shop_side.content.decode()
        assert client_user.phone not in body and driver.phone not in body

    def test_staff_always_see_the_phones(self, jobs, admin, client_user):
        for status in ("assigned", "delivered", "cancelled"):
            o = client_for(admin).get(detail(jobs[status].pk)).json()["data"]["order"]
            assert o["client"]["phone"] == client_user.phone
            assert "phone" in o["shop"]

    def test_a_direct_order_has_no_shop_phone_to_leak(self, client_user, driver):
        o = make_order(client_user, status="assigned", driver=driver)
        data = client_for(driver).get(detail(o.pk)).json()["data"]["order"]
        assert data["shop"] is None
        assert data["client"]["phone"] == client_user.phone
