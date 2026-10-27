import pytest
from django.urls import reverse

from apps.locations.models import Location
from apps.users.tests.conftest import PASSWORD

from .conftest import client_for, make_order

pytestmark = pytest.mark.django_db
CODES = {
    "pending_approval": "account_pending",
    "rejected": "account_rejected",
    "deactivated": "account_deactivated",
}


@pytest.fixture
def live_shop(trader, shop):
    shop.is_available = True
    shop.save()
    Location.objects.create(owner=trader, name="Main", address="12 Nile St")
    return shop


@pytest.mark.parametrize("status", list(CODES))
class TestBlockedTrader:
    def test_cannot_log_in_and_gets_the_clear_code(self, status, trader):
        trader.status = status
        trader.save()
        from rest_framework.test import APIClient

        r = APIClient().post(
            reverse("token"),
            {"username_or_phone": trader.username, "password": PASSWORD},
            format="json",
        )
        assert r.status_code == 403
        assert r.json()["code"] == CODES[status]

    def test_a_token_from_before_the_change_stops_working(self, status, trader):
        c = client_for(trader)
        assert c.get(reverse("shop")).status_code == 200
        trader.status = status
        trader.save()
        for name in ("shop", "location-list", "shop-item-list", "order-list"):
            r = c.get(reverse(name))
            assert r.status_code == 403, name
        assert r.json()["code"] in CODES.values()

    def test_the_shop_disappears_for_clients(
        self, status, trader, live_shop, client_user
    ):
        c = client_for(client_user)
        assert c.get(reverse("public-shop-list")).json()["data"]["count"] == 1
        trader.status = status
        trader.save()
        assert c.get(reverse("public-shop-list")).json()["data"]["count"] == 0
        assert (
            c.get(reverse("public-shop-detail", args=[live_shop.pk])).status_code == 404
        )

    def test_clients_cannot_order_from_it(self, status, trader, live_shop, client_user):
        from apps.shops.models import ShopItem

        item = ShopItem.objects.create(shop=live_shop, name="Pie")
        trader.status = status
        trader.save()
        r = client_for(client_user).post(
            reverse("order-list"),
            {
                "shop": live_shop.pk,
                "items": [{"item": item.pk, "quantity": 1}],
                "delivery": {"name": "Home", "address": "5 Garden St"},
            },
            format="json",
        )
        assert r.status_code == 400 and "shop" in r.json()["errors"]

    def test_staff_still_see_the_traders_existing_orders(
        self, status, trader, live_shop, client_user, admin, manager
    ):
        o = make_order(client_user, shop=live_shop, status="available")
        trader.status = status
        trader.save()
        for staff in (admin, manager):
            r = client_for(staff).get(reverse("order-detail", args=[o.pk]))
            assert r.status_code == 200
            assert r.json()["data"]["order"]["shop"]["name"] == live_shop.name


def test_reactivating_the_trader_restores_everything(trader, live_shop, client_user):
    trader.status = "deactivated"
    trader.save()
    c = client_for(client_user)
    assert c.get(reverse("public-shop-list")).json()["data"]["count"] == 0
    trader.status = "active"
    trader.save()
    assert c.get(reverse("public-shop-list")).json()["data"]["count"] == 1
