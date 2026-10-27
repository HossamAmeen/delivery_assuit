import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.locations.models import Location
from apps.shops import services
from apps.shops.models import Shop

from .conftest import client_for, make_user

pytestmark = pytest.mark.django_db
URL = "shop"


def get(client):
    return client.get(reverse(URL))


def patch(client, **body):
    return client.patch(reverse(URL), body, format="json")


class TestAccess:
    def test_anonymous_is_401(self):
        assert APIClient().get(reverse(URL)).status_code == 401

    @pytest.mark.parametrize("role", ["client", "driver", "manager", "admin"])
    def test_other_roles_are_403(self, role):
        c = client_for(make_user(f"u_{role}", role, "01099990001"))
        assert get(c).status_code == 403
        assert patch(c, name="Hack").status_code == 403


class TestProfile:
    def test_first_read_creates_an_unavailable_shop_from_the_account(
        self, trader_client, trader
    ):
        shop = get(trader_client).json()["data"]["shop"]
        assert shop["name"] == trader.full_name
        assert shop["phone"] == trader.phone
        assert shop["is_available"] is False
        assert shop["can_accept_orders"] is False
        assert Shop.objects.filter(owner=trader).count() == 1

    def test_second_read_does_not_create_another(self, trader_client, trader):
        get(trader_client)
        get(trader_client)
        assert Shop.objects.filter(owner=trader).count() == 1

    def test_edit_name_phone_description(self, trader_client):
        r = patch(
            trader_client,
            name="  Ahmed Store ",
            phone="+20 100-555-6677",
            description="Pies",
        )
        shop = r.json()["data"]["shop"]
        assert shop["name"] == "Ahmed Store"
        assert shop["phone"] == "201005556677"
        assert shop["description"] == "Pies"

    def test_arabic_indic_phone_is_normalised(self, trader_client):
        shop = patch(trader_client, phone="٠١٠٠١٢٣٤٥٦٧").json()["data"]["shop"]
        assert shop["phone"] == "01001234567"

    def test_phone_may_be_cleared_and_is_not_unique(
        self, trader_client, trader2_client, trader
    ):
        assert patch(trader_client, phone="").json()["data"]["shop"]["phone"] == ""
        patch(trader_client, phone="01001112222")
        assert patch(trader2_client, phone="01001112222").status_code == 200

    @pytest.mark.parametrize("phone", ["123", "abcdefgh", "1" * 16])
    def test_bad_phone(self, trader_client, phone):
        r = patch(trader_client, phone=phone)
        assert r.status_code == 400
        assert "phone" in r.json()["errors"]

    @pytest.mark.parametrize("name", ["", "a", "x" * 101])
    def test_bad_name(self, trader_client, name):
        assert "name" in patch(trader_client, name=name).json()["errors"]

    def test_description_limit(self, trader_client):
        assert patch(trader_client, description="x" * 501).status_code == 400

    def test_can_accept_orders_and_id_are_read_only(self, trader_client):
        r = patch(trader_client, can_accept_orders=True, id=99)
        shop = r.json()["data"]["shop"]
        assert shop["can_accept_orders"] is False
        assert shop["id"] != 99

    def test_another_trader_never_sees_this_shop(self, trader_client, trader2_client):
        patch(trader_client, name="Mine")
        assert get(trader2_client).json()["data"]["shop"]["name"] != "Mine"


class TestOrderable:
    def open_shop(self, client):
        patch(client, is_available=True)

    def add_pickup(self, trader, **extra):
        return Location.objects.create(
            owner=trader, name="Main", address="12 Nile St", is_pickup=True, **extra
        )

    def test_needs_available_and_a_pickup_location(self, trader_client, trader):
        self.open_shop(trader_client)
        shop = Shop.objects.get(owner=trader)
        assert services.is_shop_orderable(shop) is False
        self.add_pickup(trader)
        assert services.is_shop_orderable(shop) is True
        assert get(trader_client).json()["data"]["shop"]["can_accept_orders"] is True

    def test_closed_shop_is_not_orderable(self, trader_client, trader):
        get(trader_client)
        self.add_pickup(trader)
        assert services.is_shop_orderable(Shop.objects.get(owner=trader)) is False

    def test_delivery_only_or_deleted_location_does_not_count(
        self, trader_client, trader
    ):
        self.open_shop(trader_client)
        Location.objects.create(
            owner=trader,
            name="D",
            address="addr here",
            is_pickup=False,
            is_delivery=True,
        )
        pickup = self.add_pickup(trader)
        pickup.soft_delete()
        assert services.is_shop_orderable(Shop.objects.get(owner=trader)) is False

    @pytest.mark.parametrize("status", ["pending_approval", "rejected", "deactivated"])
    def test_non_active_owner_is_not_orderable(self, trader_client, trader, status):
        self.open_shop(trader_client)
        self.add_pickup(trader)
        trader.status = status
        trader.save()
        assert services.is_shop_orderable(Shop.objects.get(owner=trader)) is False

    def test_pickup_locations_default_first_and_own_only(self, trader, trader2):
        a = self.add_pickup(trader)
        b = self.add_pickup(trader, is_default_pickup=True)
        self.add_pickup(trader2)
        shop = services.get_or_create_shop(trader)
        assert list(services.pickup_locations(shop)) == [b, a]
