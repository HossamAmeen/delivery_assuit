import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.orders import execute
from apps.orders.models import Order, OrderStatusChange

from .conftest import client_for, make_order, make_user

pytestmark = pytest.mark.django_db


def advance(c, pk):
    return c.post(reverse("order-advance", args=[pk]))


@pytest.fixture
def mine(client_user, shop, driver):
    return make_order(client_user, shop=shop, status="assigned", driver=driver)


class TestAccess:
    def test_anonymous_is_401(self, mine):
        assert (
            APIClient().post(reverse("order-advance", args=[mine.pk])).status_code
            == 401
        )

    @pytest.mark.parametrize("role", ["admin", "manager", "client", "trader"])
    def test_only_drivers_can_use_it(self, role, mine, request):
        if role in ("client", "trader"):
            user = request.getfixturevalue(
                "client_user" if role == "client" else "trader"
            )
        else:
            user = request.getfixturevalue(role)
        assert advance(client_for(user), mine.pk).status_code == 403
        assert Order.objects.get(pk=mine.pk).status == "assigned"

    def test_another_driver_gets_404_and_nothing_changes(self, mine, driver2):
        assert advance(client_for(driver2), mine.pk).status_code == 404
        assert Order.objects.get(pk=mine.pk).status == "assigned"

    def test_unknown_order_is_404(self, driver):
        assert advance(client_for(driver), 9999).status_code == 404

    def test_an_inactive_driver_is_refused(self, mine, driver):
        c = client_for(driver)
        driver.status = "deactivated"
        driver.save()
        assert advance(c, mine.pk).status_code == 403


class TestSteps:
    def test_three_taps_deliver_the_order_in_order(self, mine, driver):
        c = client_for(driver)
        seen = []
        for expected in ("picked_up", "in_delivery", "delivered"):
            r = advance(c, mine.pk)
            assert r.status_code == 200
            seen.append(r.json()["data"]["order"]["status"])
            assert seen[-1] == expected
        rows = OrderStatusChange.objects.filter(order=mine, actor=driver)
        assert [r.to_status for r in rows] == ["picked_up", "in_delivery", "delivered"]

    def test_fourth_tap_is_refused_and_a_delivered_order_never_changes(
        self, mine, driver
    ):
        c = client_for(driver)
        for _ in range(3):
            advance(c, mine.pk)
        r = advance(c, mine.pk)
        assert r.status_code == 400
        assert "status" in r.json()["errors"]
        assert Order.objects.get(pk=mine.pk).status == "delivered"
        assert OrderStatusChange.objects.filter(order=mine, actor=driver).count() == 3

    @pytest.mark.parametrize(
        "status", ["created", "available", "cancelled", "delivered"]
    )
    def test_orders_not_in_execution_cannot_be_advanced(
        self, status, client_user, driver
    ):
        o = make_order(
            client_user,
            status=status,
            driver=driver if status in ("delivered", "cancelled") else None,
        )
        r = advance(client_for(driver), o.pk)
        # created/available orders are not visible to a driver at all
        assert r.status_code == (404 if status in ("created", "available") else 400)
        assert Order.objects.get(pk=o.pk).status == status

    def test_a_cancelled_order_cannot_be_advanced_by_its_old_driver(
        self, mine, driver, admin
    ):
        from apps.orders import lifecycle

        lifecycle.transition(mine, "cancelled", admin, reason="stop")
        r = advance(client_for(driver), mine.pk)
        assert r.status_code == 400
        assert Order.objects.get(pk=mine.pk).status == "cancelled"

    def test_each_step_response_has_the_updated_order(self, mine, driver):
        r = advance(client_for(driver), mine.pk)
        data = r.json()["data"]["order"]
        assert data["id"] == mine.pk and data["status"] == "picked_up"


def test_next_action_names():
    class O:  # minimal stand-in
        status = None

    o = O()
    names = {}
    for status in Order.Status:
        o.status = status
        names[status.value] = execute.next_action(o)
    assert names == {
        "created": None,
        "available": None,
        "assigned": "pick_up",
        "picked_up": "start_delivery",
        "in_delivery": "deliver",
        "delivered": None,
        "cancelled": None,
    }


def test_the_driver_is_free_after_delivery(mine, driver, admin, client_user, shop):
    from apps.orders import assign

    other = make_order(client_user, shop=shop, status="available")
    c = client_for(driver)
    assert assign.has_active_order(driver)
    for _ in range(3):
        advance(c, mine.pk)
    assert not assign.has_active_order(driver)
    assign.assign(other, admin, driver.pk)


def test_make_user_import_is_used():
    assert make_user
