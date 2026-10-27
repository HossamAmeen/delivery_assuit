import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.locations.models import Location
from apps.orders import lifecycle
from apps.orders.models import Order, OrderFeeChange, OrderItem
from apps.shops.models import ShopItem

from .conftest import client_for, make_order, make_user

pytestmark = pytest.mark.django_db


def set_price(c, pk, price):
    return c.patch(
        reverse("staff-item-price", args=[pk]), {"price": price}, format="json"
    )


def set_fee(c, pk, fee):
    return c.patch(
        reverse("order-fee", args=[pk]), {"delivery_fee": fee}, format="json"
    )


@pytest.fixture
def item(shop):
    return ShopItem.objects.create(shop=shop, name="Cheese pie")


class TestItemPrice:
    def test_anonymous_is_401(self, item):
        r = APIClient().patch(
            reverse("staff-item-price", args=[item.pk]), {"price": 1}, format="json"
        )
        assert r.status_code == 401

    @pytest.mark.parametrize("role", ["trader", "client", "driver"])
    def test_only_staff_can_set_prices(self, role, item):
        c = client_for(make_user(f"u_{role}", role, "01099990001"))
        assert set_price(c, item.pk, 10).status_code == 403
        item.refresh_from_db()
        assert item.price is None

    def test_the_traders_own_item_endpoint_cannot_set_a_price(
        self, trader_client, item
    ):
        r = trader_client.patch(
            reverse("shop-item-detail", args=[item.pk]), {"price": 99}, format="json"
        )
        assert r.json()["data"]["item"]["price"] is None

    @pytest.mark.parametrize("who", ["admin", "manager"])
    def test_staff_set_and_clear_a_price_with_audit(self, who, item, request):
        staff = request.getfixturevalue(who)
        c = client_for(staff)
        r = set_price(c, item.pk, 12.5)
        assert r.status_code == 200
        data = r.json()["data"]["item"]
        assert data["price"] == 12.5 and data["shop"]["id"] == item.shop_id
        item.refresh_from_db()
        assert item.price_set_by_id == staff.pk and item.price_set_at
        assert set_price(c, item.pk, None).json()["data"]["item"]["price"] is None

    @pytest.mark.parametrize("bad", [-1, 100001, "abc", 1.234])
    def test_bad_prices_are_refused(self, admin, item, bad):
        r = set_price(client_for(admin), item.pk, bad)
        assert r.status_code == 400 and "price" in r.json()["errors"]

    def test_unknown_item_is_404(self, admin):
        assert set_price(client_for(admin), 9999, 5).status_code == 404

    def test_clients_see_the_price_on_shop_details(
        self, admin, item, trader, client_user
    ):
        trader.shop.is_available = True
        trader.shop.save()
        Location.objects.create(owner=trader, name="Main", address="12 Nile St")
        set_price(client_for(admin), item.pk, 20)
        data = (
            client_for(client_user)
            .get(reverse("public-shop-detail", args=[trader.shop.pk]))
            .json()
        )
        assert data["data"]["shop"]["items"][0]["price"] == 20


class TestSnapshot:
    def place(self, client_user, shop, item):
        c = client_for(client_user)
        return c.post(
            reverse("order-list"),
            {
                "shop": shop.pk,
                "items": [{"item": item.pk, "quantity": 3}],
                "delivery": {"name": "Home", "address": "5 Garden St"},
            },
            format="json",
        ).json()["data"]["order"]

    @pytest.fixture(autouse=True)
    def open_shop(self, shop, trader):
        shop.is_available = True
        shop.save()
        Location.objects.create(owner=trader, name="Main", address="12 Nile St")

    def test_price_is_stored_on_the_line_and_totalled(
        self, client_user, shop, item, admin
    ):
        set_price(client_for(admin), item.pk, 10)
        order = self.place(client_user, shop, item)
        assert order["items"] == [{"name": "Cheese pie", "quantity": 3, "price": 10}]
        assert order["items_total"] == 30

    def test_unpriced_items_have_no_total(self, client_user, shop, item):
        order = self.place(client_user, shop, item)
        assert order["items"][0]["price"] is None and order["items_total"] is None

    def test_later_price_changes_do_not_touch_past_orders(
        self, client_user, shop, item, admin
    ):
        c = client_for(admin)
        set_price(c, item.pk, 10)
        order = self.place(client_user, shop, item)
        set_price(c, item.pk, 99)
        set_price(c, item.pk, None)
        again = (
            client_for(client_user)
            .get(reverse("order-detail", args=[order["id"]]))
            .json()
        )
        assert again["data"]["order"]["items"][0]["price"] == 10
        assert again["data"]["order"]["items_total"] == 30

    def test_total_ignores_unpriced_lines(self, client_user, shop):
        o = make_order(client_user, shop=shop)
        OrderItem.objects.create(order=o, name="A", quantity=2, unit_price="5.50")
        OrderItem.objects.create(order=o, name="B", quantity=1)
        data = client_for(client_user).get(reverse("order-detail", args=[o.pk])).json()
        assert data["data"]["order"]["items_total"] == 11


class TestFee:
    @pytest.mark.parametrize("role", ["trader", "client", "driver"])
    def test_only_staff_can_set_fees(self, role, order):
        c = client_for(make_user(f"u_{role}", role, "01099990001"))
        assert set_fee(c, order.pk, 10).status_code == 403
        assert Order.objects.get(pk=order.pk).delivery_fee is None

    def test_the_client_cannot_send_a_fee_when_creating(self, order, client_user):
        assert set_fee(client_for(client_user), order.pk, 1).status_code == 403

    @pytest.mark.parametrize(
        "status", ["created", "available", "assigned", "picked_up", "in_delivery"]
    )
    def test_staff_can_set_and_change_until_delivered(
        self, status, admin, manager, client_user, driver
    ):
        o = make_order(
            client_user,
            status=status,
            driver=driver if status not in ("created", "available") else None,
        )
        r1 = set_fee(client_for(admin), o.pk, 20)
        r2 = set_fee(client_for(manager), o.pk, 25.5)
        assert r1.status_code == r2.status_code == 200
        assert r2.json()["data"]["order"]["delivery_fee"] == 25.5
        rows = list(OrderFeeChange.objects.filter(order=o))
        assert [(str(r.old_fee), str(r.new_fee), r.actor_id) for r in rows] == [
            ("None", "20.00", admin.pk),
            ("20.00", "25.50", manager.pk),
        ]
        assert all(r.created_at for r in rows)

    @pytest.mark.parametrize("status", ["delivered", "cancelled"])
    def test_finished_orders_are_closed(self, status, admin, client_user, driver):
        o = make_order(
            client_user,
            status=status,
            driver=driver if status == "delivered" else None,
            delivery_fee="10",
        )
        r = set_fee(client_for(admin), o.pk, 99)
        assert r.status_code == 400 and "status" in r.json()["errors"]
        assert str(Order.objects.get(pk=o.pk).delivery_fee) == "10.00"
        assert OrderFeeChange.objects.filter(order=o).count() == 0

    @pytest.mark.parametrize("bad", [-1, 100001, "x", 1.234, None])
    def test_bad_fee(self, admin, order, bad):
        r = set_fee(client_for(admin), order.pk, bad)
        assert r.status_code == 400 and "delivery_fee" in r.json()["errors"]

    def test_approve_records_the_fee_change(self, admin, order):
        client_for(admin).post(
            reverse("order-approve", args=[order.pk]),
            {"delivery_fee": 15},
            format="json",
        )
        row = OrderFeeChange.objects.get(order=order)
        assert (row.old_fee, str(row.new_fee), row.actor_id) == (
            None,
            "15.00",
            admin.pk,
        )

    def test_client_sees_the_fee(self, admin, order, client_user):
        set_fee(client_for(admin), order.pk, 12)
        data = (
            client_for(client_user).get(reverse("order-detail", args=[order.pk])).json()
        )
        assert data["data"]["order"]["delivery_fee"] == 12

    def test_unknown_order_is_404(self, admin):
        assert set_fee(client_for(admin), 9999, 5).status_code == 404

    def test_lifecycle_helper_import(self):
        assert lifecycle
