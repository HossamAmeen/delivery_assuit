import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.orders import lifecycle
from apps.orders.models import Order, OrderStatusChange

from .conftest import client_for, make_order, make_user

pytestmark = pytest.mark.django_db


def approve(c, pk, **body):
    return c.post(reverse("order-approve", args=[pk]), body, format="json")


def reject(c, pk, **body):
    return c.post(reverse("order-reject", args=[pk]), body, format="json")


class TestAccess:
    def test_anonymous_is_401(self, order):
        assert (
            APIClient().post(reverse("order-approve", args=[order.pk])).status_code
            == 401
        )

    @pytest.mark.parametrize("role", ["client", "trader", "driver"])
    def test_other_roles_are_403_and_change_nothing(self, role, order):
        c = client_for(make_user(f"u_{role}", role, "01099990001"))
        assert approve(c, order.pk).status_code == 403
        assert reject(c, order.pk, reason="nope nope").status_code == 403
        assert Order.objects.get(pk=order.pk).status == "created"

    def test_the_owning_client_cannot_approve_their_own_order(self, order, client_user):
        assert approve(client_for(client_user), order.pk).status_code == 403

    def test_unknown_order_is_404(self, admin):
        assert approve(client_for(admin), 9999).status_code == 404


@pytest.mark.parametrize("who", ["admin", "manager"])
class TestApprove:
    def test_makes_the_order_available_and_records_who(self, who, order, request):
        staff = request.getfixturevalue(who)
        r = approve(client_for(staff), order.pk)
        assert r.status_code == 200
        data = r.json()["data"]["order"]
        assert data["status"] == "available"
        assert data["delivery_fee"] is None
        row = OrderStatusChange.objects.filter(order=order).last()
        assert (row.to_status, row.actor_id) == ("available", staff.pk)
        assert row.created_at

    def test_stores_the_fee(self, who, order, request):
        c = client_for(request.getfixturevalue(who))
        data = approve(c, order.pk, delivery_fee=25.5).json()["data"]["order"]
        assert data["delivery_fee"] == 25.5
        assert str(Order.objects.get(pk=order.pk).delivery_fee) == "25.50"

    @pytest.mark.parametrize("fee", [-1, 100001, "abc", 1.234, 123456789])
    def test_bad_fee_is_rejected_and_nothing_changes(self, who, order, request, fee):
        c = client_for(request.getfixturevalue(who))
        r = approve(c, order.pk, delivery_fee=fee)
        assert r.status_code == 400
        assert "delivery_fee" in r.json()["errors"]
        assert Order.objects.get(pk=order.pk).status == "created"

    def test_zero_fee_is_allowed(self, who, order, request):
        c = client_for(request.getfixturevalue(who))
        assert (
            approve(c, order.pk, delivery_fee=0).json()["data"]["order"]["delivery_fee"]
            == 0
        )

    def test_second_approve_is_400_and_keeps_the_first_fee(self, who, order, request):
        c = client_for(request.getfixturevalue(who))
        approve(c, order.pk, delivery_fee=10)
        r = approve(c, order.pk, delivery_fee=99)
        assert r.status_code == 400
        assert "status" in r.json()["errors"]
        assert str(Order.objects.get(pk=order.pk).delivery_fee) == "10.00"
        assert (
            OrderStatusChange.objects.filter(order=order, to_status="available").count()
            == 1
        )


@pytest.mark.parametrize("who", ["admin", "manager"])
class TestReject:
    def test_cancels_with_reason_visible_to_the_client(
        self, who, order, client_user, request
    ):
        staff = request.getfixturevalue(who)
        r = reject(client_for(staff), order.pk, reason="Address is unclear")
        assert r.status_code == 200
        assert r.json()["data"]["order"]["status"] == "cancelled"
        mine = client_for(client_user).get(reverse("order-detail", args=[order.pk]))
        data = mine.json()["data"]["order"]
        assert data["cancel_reason"] == "Address is unclear"
        assert data["cancelled_at"]
        assert Order.objects.get(pk=order.pk).cancelled_by_id == staff.pk

    @pytest.mark.parametrize("reason", [None, "", "  ", "ab", "x" * 501])
    def test_reason_is_required(self, who, order, request, reason):
        c = client_for(request.getfixturevalue(who))
        body = {} if reason is None else {"reason": reason}
        r = reject(c, order.pk, **body)
        assert r.status_code == 400
        assert "reason" in r.json()["errors"]
        assert Order.objects.get(pk=order.pk).status == "created"

    def test_repeat_is_400_and_one_history_row(self, who, order, request):
        c = client_for(request.getfixturevalue(who))
        reject(c, order.pk, reason="not valid")
        assert reject(c, order.pk, reason="again again").status_code == 400
        assert (
            OrderStatusChange.objects.filter(order=order, to_status="cancelled").count()
            == 1
        )

    def test_rejected_order_never_reaches_the_trader(self, who, order, trader, request):
        reject(client_for(request.getfixturevalue(who)), order.pk, reason="not valid")
        assert (
            client_for(trader).get(reverse("order-list")).json()["data"]["count"] == 0
        )


class TestWrongState:
    @pytest.mark.parametrize(
        "status",
        ["available", "assigned", "picked_up", "in_delivery", "delivered", "cancelled"],
    )
    def test_only_a_created_order_can_be_reviewed(
        self, status, admin, client_user, driver
    ):
        o = make_order(client_user, status=status, driver=driver)
        c = client_for(admin)
        assert approve(c, o.pk).status_code == 400
        assert reject(c, o.pk, reason="too late").status_code == 400
        assert Order.objects.get(pk=o.pk).status == status


def test_approved_order_becomes_visible_to_the_trader(order, admin, trader):
    c = client_for(trader)
    assert c.get(reverse("order-list")).json()["data"]["count"] == 0
    approve(client_for(admin), order.pk, delivery_fee=12)
    rows = c.get(reverse("order-list")).json()["data"]["results"]
    assert [r["id"] for r in rows] == [order.pk]
    assert "phone" not in rows[0]["client"]


def test_pending_review_list_for_staff(admin, client_user):
    a = make_order(client_user)
    b = make_order(client_user)
    lifecycle.transition(b, "available", admin)
    rows = (
        client_for(admin)
        .get(reverse("order-list"), {"status": "created"})
        .json()["data"]["results"]
    )
    assert [r["id"] for r in rows] == [a.pk]
    assert rows[0]["client"]["phone"] == client_user.phone
