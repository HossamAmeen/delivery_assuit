import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.locations.models import Location
from apps.shops import services
from apps.shops.models import ShopItem

from .conftest import client_for, make_user

pytestmark = pytest.mark.django_db
LIST = "public-shop-list"


def detail(pk):
    return reverse("public-shop-detail", args=[pk])


def open_shop(trader, name="Ahmed Store", pickup=True, **extra):
    shop = services.get_or_create_shop(trader)
    shop.name = name
    shop.is_available = True
    for k, v in extra.items():
        setattr(shop, k, v)
    shop.save()
    if pickup:
        Location.objects.create(
            owner=trader, name="Main", address="12 Nile St", is_default_pickup=True
        )
    return shop


@pytest.fixture
def shopper(client_user):
    return client_for(client_user)


def names(response):
    return [s["name"] for s in response.json()["data"]["results"]]


class TestAccess:
    def test_anonymous_is_401(self):
        assert APIClient().get(reverse(LIST)).status_code == 401

    @pytest.mark.parametrize("role", ["trader", "driver", "manager", "admin"])
    def test_other_roles_are_403(self, role):
        c = client_for(make_user(f"u_{role}", role, "01099990001"))
        assert c.get(reverse(LIST)).status_code == 403
        assert c.get(detail(1)).status_code == 403


class TestList:
    def test_lists_only_orderable_shops_with_id_name_description(self, shopper, trader):
        open_shop(trader, description="Pies")
        rows = shopper.get(reverse(LIST)).json()["data"]["results"]
        assert rows == [
            {"id": trader.shop.pk, "name": "Ahmed Store", "description": "Pies"}
        ]

    def test_no_phone_anywhere(self, shopper, trader):
        open_shop(trader, phone="01001234567")
        assert "01001234567" not in shopper.get(reverse(LIST)).content.decode()
        sid = trader.shop.pk
        assert "01001234567" not in shopper.get(detail(sid)).content.decode()

    def test_hides_closed_shops_and_shops_without_pickup(
        self, shopper, trader, trader2
    ):
        open_shop(trader, is_available=False)
        open_shop(trader2, name="No pickup", pickup=False)
        assert names(shopper.get(reverse(LIST))) == []

    def test_delivery_only_or_deleted_locations_do_not_count(self, shopper, trader):
        open_shop(trader, pickup=False)
        Location.objects.create(
            owner=trader,
            name="D",
            address="addr here",
            is_pickup=False,
            is_delivery=True,
        )
        gone = Location.objects.create(owner=trader, name="G", address="addr here")
        gone.soft_delete()
        assert names(shopper.get(reverse(LIST))) == []

    @pytest.mark.parametrize("status", ["pending_approval", "rejected", "deactivated"])
    def test_non_active_trader_shops_are_hidden(self, shopper, trader, status):
        open_shop(trader)
        trader.status = status
        trader.save()
        assert names(shopper.get(reverse(LIST))) == []

    def test_search_by_name_and_sorted(self, shopper, trader, trader2):
        open_shop(trader, name="Zeta Bakery")
        open_shop(trader2, name="Alpha Grill")
        assert names(shopper.get(reverse(LIST))) == ["Alpha Grill", "Zeta Bakery"]
        assert names(shopper.get(reverse(LIST), {"search": "bake"})) == ["Zeta Bakery"]
        assert names(shopper.get(reverse(LIST), {"search": "nothing"})) == []

    def test_empty_list_is_ok(self, shopper):
        data = shopper.get(reverse(LIST)).json()["data"]
        assert data["count"] == 0


class TestDetail:
    def test_items_and_pickup_locations(self, shopper, trader):
        shop = open_shop(trader)
        second = Location.objects.create(
            owner=trader, name="Second", address="2 Side St"
        )
        ShopItem.objects.create(shop=shop, name="Cheese pie")
        ShopItem.objects.create(shop=shop, name="Secret", is_hidden=True)
        gone = ShopItem.objects.create(shop=shop, name="Deleted")
        gone.soft_delete()
        data = shopper.get(detail(shop.pk)).json()["data"]["shop"]
        assert [i["name"] for i in data["items"]] == ["Cheese pie"]
        assert data["items"][0]["price"] is None
        assert [(p["name"], p["is_default"]) for p in data["pickup_locations"]] == [
            ("Main", True),
            ("Second", False),
        ]
        assert second.pk in [p["id"] for p in data["pickup_locations"]]

    def test_item_price_is_returned_when_set(self, shopper, trader):
        shop = open_shop(trader)
        ShopItem.objects.create(shop=shop, name="Priced", price="12.50")
        data = shopper.get(detail(shop.pk)).json()["data"]["shop"]
        assert data["items"][0]["price"] == 12.5

    def test_other_traders_data_is_never_mixed_in(self, shopper, trader, trader2):
        a = open_shop(trader)
        b = open_shop(trader2, name="Other")
        ShopItem.objects.create(shop=b, name="Theirs")
        data = shopper.get(detail(a.pk)).json()["data"]["shop"]
        assert data["items"] == []

    def test_closed_or_unknown_shop_is_404(self, shopper, trader):
        shop = open_shop(trader)
        shop.is_available = False
        shop.save()
        assert shopper.get(detail(shop.pk)).status_code == 404
        assert shopper.get(detail(9999)).status_code == 404

    def test_a_shop_that_closes_disappears(self, shopper, trader):
        shop = open_shop(trader)
        assert shopper.get(detail(shop.pk)).status_code == 200
        shop.is_available = False
        shop.save()
        assert shopper.get(detail(shop.pk)).status_code == 404


def test_queryset_and_helper_agree(trader, trader2):
    a = open_shop(trader)
    b = open_shop(trader2, name="Closed", is_available=False)
    live = set(services.orderable_shops().values_list("pk", flat=True))
    assert live == {a.pk}
    assert services.is_shop_orderable(a) and not services.is_shop_orderable(b)
