import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.orders import assign
from apps.orders.models import Order, OrderStatusChange

from .conftest import client_for, make_order, make_user

pytestmark = pytest.mark.django_db


def cancel(c, pk, **body):
    return c.post(reverse("order-cancel", args=[pk]), body, format="json")


def job(client_user, status, driver=None):
    return make_order(
        client_user,
        status=status,
        driver=driver
        if status in ("assigned", "picked_up", "in_delivery", "delivered")
        else None,
    )


def test_anonymous_is_401(order):
    assert APIClient().post(reverse("order-cancel", args=[order.pk])).status_code == 401


class TestClient:
    @pytest.mark.parametrize("status", ["created", "available"])
    def test_owner_cancels_before_assignment_with_or_without_a_reason(
        self, status, client_user
    ):
        o = job(client_user, status)
        r = cancel(client_for(client_user), o.pk)
        assert r.status_code == 200
        data = r.json()["data"]["order"]
        assert data["status"] == "cancelled" and data["cancelled_at"]
        row = OrderStatusChange.objects.filter(order=o).last()
        assert (row.to_status, row.actor_id) == ("cancelled", client_user.pk)
        assert Order.objects.get(pk=o.pk).cancelled_by_id == client_user.pk

    def test_owner_may_give_a_reason(self, client_user):
        o = job(client_user, "available")
        data = cancel(client_for(client_user), o.pk, reason="Changed my mind").json()[
            "data"
        ]["order"]
        assert data["cancel_reason"] == "Changed my mind"

    @pytest.mark.parametrize("status", ["assigned", "picked_up", "in_delivery"])
    def test_after_assignment_the_client_cannot_cancel(
        self, status, client_user, driver
    ):
        o = job(client_user, status, driver)
        assert cancel(client_for(client_user), o.pk).status_code == 403
        assert Order.objects.get(pk=o.pk).status == status

    @pytest.mark.parametrize("status", ["delivered", "cancelled"])
    def test_finished_orders_cannot_be_cancelled(self, status, client_user, driver):
        o = job(client_user, status, driver)
        r = cancel(client_for(client_user), o.pk)
        assert r.status_code == 400 and "status" in r.json()["errors"]

    def test_another_clients_order_is_404(self, order, client2):
        assert cancel(client_for(client2), order.pk).status_code == 404
        assert Order.objects.get(pk=order.pk).status == "created"

    @pytest.mark.parametrize("role", ["trader", "driver"])
    def test_traders_and_drivers_cannot_cancel(
        self, role, order, trader, driver, admin
    ):
        from apps.orders import lifecycle

        lifecycle.transition(order, "available", admin)
        user = trader if role == "trader" else driver
        r = cancel(client_for(user), order.pk, reason="because")
        assert r.status_code in (403, 404)
        assert Order.objects.get(pk=order.pk).status == "available"


@pytest.mark.parametrize("who", ["admin", "manager"])
class TestStaff:
    @pytest.mark.parametrize(
        "status", ["created", "available", "assigned", "picked_up", "in_delivery"]
    )
    def test_staff_cancel_any_unfinished_order_with_a_reason(
        self, who, status, client_user, driver, request
    ):
        staff = request.getfixturevalue(who)
        o = job(client_user, status, driver)
        r = cancel(client_for(staff), o.pk, reason="Customer unreachable")
        assert r.status_code == 200
        assert r.json()["data"]["order"]["cancel_reason"] == "Customer unreachable"
        assert Order.objects.get(pk=o.pk).cancelled_by_id == staff.pk

    @pytest.mark.parametrize("reason", [None, "", "  ", "ab"])
    def test_staff_must_give_a_reason(self, who, reason, order, request):
        c = client_for(request.getfixturevalue(who))
        body = {} if reason is None else {"reason": reason}
        r = cancel(c, order.pk, **body)
        assert r.status_code == 400 and "reason" in r.json()["errors"]
        assert Order.objects.get(pk=order.pk).status == "created"

    @pytest.mark.parametrize("status", ["delivered", "cancelled"])
    def test_delivered_and_cancelled_are_final(
        self, who, status, client_user, driver, request
    ):
        o = job(client_user, status, driver)
        r = cancel(client_for(request.getfixturevalue(who)), o.pk, reason="too late")
        assert r.status_code == 400
        assert Order.objects.get(pk=o.pk).status == status

    def test_cancelling_frees_the_driver_and_shows_in_their_history(
        self, who, client_user, driver, request
    ):
        o = job(client_user, "assigned", driver)
        assert assign.has_active_order(driver)
        cancel(client_for(request.getfixturevalue(who)), o.pk, reason="Stopped")
        assert not assign.has_active_order(driver)
        mine = (
            client_for(driver)
            .get(reverse("order-list"), {"scope": "history"})
            .json()["data"]["results"]
        )
        assert [x["id"] for x in mine] == [o.pk]
        assert mine[0]["cancel_reason"] == "Stopped"

    def test_the_old_driver_can_no_longer_advance_it(
        self, who, client_user, driver, request
    ):
        o = job(client_user, "assigned", driver)
        cancel(client_for(request.getfixturevalue(who)), o.pk, reason="Stopped")
        assert (
            client_for(driver).post(reverse("order-advance", args=[o.pk])).status_code
            == 400
        )

    def test_no_release_flow_exists_for_drivers(
        self, who, client_user, driver, request
    ):
        o = job(client_user, "assigned", driver)
        c = client_for(driver)
        assert cancel(c, o.pk, reason="I quit").status_code == 403
        assert Order.objects.get(pk=o.pk).driver_id == driver.pk


def test_make_user_is_importable():
    assert make_user
