import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.locations.models import Location, SavedAddress
from apps.orders.models import Order, OrderStatusChange
from apps.shops.models import ShopItem
from apps.shops.services import get_or_create_shop

from .conftest import client_for, make_user

pytestmark = pytest.mark.django_db
URL = "order-list"
HOME = {"name": "Home", "address": "5 Garden St", "latitude": 30.05, "longitude": 31.23}


@pytest.fixture
def open_shop(trader):
    shop = get_or_create_shop(trader)
    shop.is_available = True
    shop.save()
    loc = Location.objects.create(
        owner=trader, name="Main", address="12 Nile St", is_default_pickup=True
    )
    shop.default_loc = loc
    return shop


@pytest.fixture
def item(open_shop):
    return ShopItem.objects.create(shop=open_shop, name="Cheese pie")


@pytest.fixture
def api(client_user):
    return client_for(client_user)


def shop_body(shop, item, **extra):
    return {
        "shop": shop.pk,
        "items": [{"item": item.pk, "quantity": 2}],
        "delivery": HOME,
        **extra,
    }


def post(c, body):
    return c.post(reverse(URL), body, format="json")


class TestAccess:
    def test_anonymous_is_401(self):
        assert APIClient().post(reverse(URL), {}, format="json").status_code == 401

    @pytest.mark.parametrize("role", ["trader", "driver", "manager", "admin"])
    def test_only_clients_create_orders(self, role, open_shop, item):
        c = client_for(make_user(f"u_{role}", role, "01099990001"))
        assert post(c, shop_body(open_shop, item)).status_code == 403
        assert Order.objects.count() == 0

    def test_pending_account_is_refused(self, client_user, open_shop, item):
        c = client_for(client_user)
        client_user.status = "deactivated"
        client_user.save()
        assert post(c, shop_body(open_shop, item)).status_code == 403


class TestShopOrder:
    def test_creates_a_created_order_with_defaults(
        self, api, open_shop, item, client_user
    ):
        r = post(api, shop_body(open_shop, item, description="No onions"))
        assert r.status_code == 201
        o = r.json()["data"]["order"]
        assert o["status"] == "created"
        assert o["reference"] == f"ORD-{o['id']:06d}"
        assert o["shop"] == {"id": open_shop.pk, "name": open_shop.name}
        assert o["pickup"]["address"] == "12 Nile St"
        assert o["delivery"] == {
            "name": "Home",
            "address": "5 Garden St",
            "latitude": 30.05,
            "longitude": 31.23,
        }
        assert o["items"] == [{"name": "Cheese pie", "quantity": 2, "price": None}]
        assert o["description"] == "No onions"
        assert o["delivery_fee"] is None
        assert o["driver"] is None
        assert Order.objects.get(pk=o["id"]).client_id == client_user.pk

    def test_writes_the_first_history_row(self, api, open_shop, item, client_user):
        pk = post(api, shop_body(open_shop, item)).json()["data"]["order"]["id"]
        row = OrderStatusChange.objects.get(order_id=pk)
        assert (row.from_status, row.to_status, row.actor_id) == (
            "",
            "created",
            client_user.pk,
        )

    def test_chosen_pickup_location(self, api, open_shop, item, trader):
        other = Location.objects.create(
            owner=trader, name="Second", address="2 Side St"
        )
        o = post(api, shop_body(open_shop, item, pickup_location=other.pk)).json()[
            "data"
        ]["order"]
        assert o["pickup"]["name"] == "Second"

    def test_pickup_location_must_belong_to_the_shop_and_allow_pickup(
        self, api, open_shop, item, trader, trader2
    ):
        foreign = Location.objects.create(owner=trader2, name="X", address="far away")
        delivery_only = Location.objects.create(
            owner=trader,
            name="D",
            address="drop only",
            is_pickup=False,
            is_delivery=True,
        )
        for pk in (foreign.pk, delivery_only.pk, 9999):
            r = post(api, shop_body(open_shop, item, pickup_location=pk))
            assert r.status_code == 400
            assert "pickup_location" in r.json()["errors"]

    def test_uses_saved_address_for_delivery(self, api, open_shop, item, client_user):
        a = SavedAddress.objects.create(
            owner=client_user, name="Mum", address="9 Rose St"
        )
        body = shop_body(open_shop, item)
        del body["delivery"]
        o = post(api, {**body, "delivery_saved_address": a.pk}).json()["data"]["order"]
        assert o["delivery"]["name"] == "Mum"

    def test_place_is_a_copy_not_a_link(
        self, api, open_shop, item, client_user, trader
    ):
        a = SavedAddress.objects.create(
            owner=client_user, name="Mum", address="9 Rose St"
        )
        body = shop_body(open_shop, item)
        del body["delivery"]
        pk = post(api, {**body, "delivery_saved_address": a.pk}).json()["data"][
            "order"
        ]["id"]
        a.name, a.address = "Changed", "Elsewhere"
        a.save()
        a.soft_delete()
        open_shop.default_loc.address = "Moved away"
        open_shop.default_loc.save()
        open_shop.default_loc.soft_delete()
        o = Order.objects.get(pk=pk)
        assert (o.delivery_name, o.delivery_address) == ("Mum", "9 Rose St")
        assert o.pickup_address == "12 Nile St"

    def test_another_clients_saved_address_is_rejected_like_a_missing_one(
        self, api, open_shop, item, client2
    ):
        theirs = SavedAddress.objects.create(
            owner=client2, name="Theirs", address="secret addr"
        )
        body = shop_body(open_shop, item)
        del body["delivery"]
        r1 = post(api, {**body, "delivery_saved_address": theirs.pk})
        r2 = post(api, {**body, "delivery_saved_address": 99999})
        assert r1.status_code == r2.status_code == 400
        assert r1.json()["errors"] == r2.json()["errors"]
        assert "secret" not in r1.content.decode()

    def test_delivery_is_required_and_exclusive(
        self, api, open_shop, item, client_user
    ):
        body = shop_body(open_shop, item)
        del body["delivery"]
        assert "delivery" in post(api, body).json()["errors"]
        a = SavedAddress.objects.create(
            owner=client_user, name="Mum", address="9 Rose St"
        )
        r = post(api, {**shop_body(open_shop, item), "delivery_saved_address": a.pk})
        assert "delivery" in r.json()["errors"]

    @pytest.mark.parametrize(
        "items",
        [
            None,
            [],
            [{"item": 1, "quantity": 0}],
            [{"item": 1, "quantity": 100}],
            [{"quantity": 1}],
        ],
    )
    def test_items_are_required_and_bounded(self, api, open_shop, items):
        body = {"shop": open_shop.pk, "delivery": HOME}
        if items is not None:
            body["items"] = items
        r = post(api, body)
        assert r.status_code == 400
        assert "items" in r.json()["errors"]

    def test_items_must_belong_to_the_shop_and_be_visible(
        self, api, open_shop, item, trader2
    ):
        hidden = ShopItem.objects.create(shop=open_shop, name="Hidden", is_hidden=True)
        gone = ShopItem.objects.create(shop=open_shop, name="Gone")
        gone.soft_delete()
        foreign = ShopItem.objects.create(
            shop=get_or_create_shop(trader2), name="Foreign"
        )
        for bad in (hidden, gone, foreign):
            body = shop_body(open_shop, item)
            body["items"] = [
                {"item": item.pk, "quantity": 1},
                {"item": bad.pk, "quantity": 1},
            ]
            r = post(api, body)
            assert r.status_code == 400, bad.name
            assert "items" in r.json()["errors"]
        assert Order.objects.count() == 0

    def test_duplicate_item_lines_are_rejected(self, api, open_shop, item):
        body = shop_body(open_shop, item)
        body["items"] = [{"item": item.pk, "quantity": 1}] * 2
        assert "items" in post(api, body).json()["errors"]

    def test_too_many_lines(self, api, open_shop):
        items = [ShopItem(shop=open_shop, name=f"I{i}") for i in range(51)]
        ShopItem.objects.bulk_create(items)
        body = {
            "shop": open_shop.pk,
            "delivery": HOME,
            "items": [{"item": i.pk, "quantity": 1} for i in ShopItem.objects.all()],
        }
        assert "items" in post(api, body).json()["errors"]

    def test_closed_shop_or_missing_pickup_or_unknown_shop(self, api, open_shop, item):
        open_shop.is_available = False
        open_shop.save()
        assert "shop" in post(api, shop_body(open_shop, item)).json()["errors"]
        open_shop.is_available = True
        open_shop.save()
        Location.objects.all().delete()
        assert "shop" in post(api, shop_body(open_shop, item)).json()["errors"]
        body = shop_body(open_shop, item)
        body["shop"] = 9999
        assert "shop" in post(api, body).json()["errors"]
        assert Order.objects.count() == 0

    def test_direct_only_fields_are_refused(self, api, open_shop, item):
        r = post(api, shop_body(open_shop, item, pickup=HOME))
        assert "pickup" in r.json()["errors"]

    def test_description_is_optional_but_capped(self, api, open_shop, item):
        assert post(api, shop_body(open_shop, item)).status_code == 201
        r = post(api, shop_body(open_shop, item, description="x" * 1001))
        assert "description" in r.json()["errors"]

    def test_bad_delivery_place(self, api, open_shop, item):
        for bad in (
            {"name": "", "address": "ok addr"},
            {"name": "Ok", "address": "ab"},
            {**HOME, "latitude": 95},
            {"name": "Ok", "address": "ok addr", "latitude": 5},
        ):
            r = post(api, {**shop_body(open_shop, item), "delivery": bad})
            assert r.status_code == 400
            assert "delivery" in r.json()["errors"]

    def test_no_fee_from_the_client(self, api, open_shop, item):
        o = post(
            api,
            shop_body(open_shop, item, delivery_fee=1, status="available", driver=1),
        )
        data = o.json()["data"]["order"]
        assert data["delivery_fee"] is None
        assert data["status"] == "created"
        assert data["driver"] is None


DIRECT = {
    "pickup": {"name": "Office", "address": "1 Tahrir Sq"},
    "delivery": {"name": "Mum", "address": "9 Rose St"},
    "description": "A box of documents",
}


class TestDirectDelivery:
    def test_creates_an_order_without_a_shop(self, api):
        r = post(api, DIRECT)
        assert r.status_code == 201
        o = r.json()["data"]["order"]
        assert o["shop"] is None
        assert o["status"] == "created"
        assert o["pickup"]["name"] == "Office"
        assert o["items"] == []
        assert o["description"] == "A box of documents"

    @pytest.mark.parametrize("missing", ["pickup", "delivery", "description"])
    def test_pickup_delivery_and_details_are_mandatory(self, api, missing):
        body = {k: v for k, v in DIRECT.items() if k != missing}
        r = post(api, body)
        assert r.status_code == 400
        assert missing in r.json()["errors"]
        assert Order.objects.count() == 0

    @pytest.mark.parametrize("text", ["", "  ", "ab"])
    def test_short_details_are_refused(self, api, text):
        r = post(api, {**DIRECT, "description": text})
        assert "description" in r.json()["errors"]

    def test_both_places_can_come_from_saved_addresses(self, api, client_user):
        a = SavedAddress.objects.create(
            owner=client_user, name="Home", address="5 Garden St"
        )
        b = SavedAddress.objects.create(
            owner=client_user, name="Work", address="2 Side St"
        )
        r = post(
            api,
            {
                "pickup_saved_address": a.pk,
                "delivery_saved_address": b.pk,
                "description": "Keys",
            },
        )
        assert r.status_code == 201
        o = r.json()["data"]["order"]
        assert (o["pickup"]["name"], o["delivery"]["name"]) == ("Home", "Work")

    def test_shop_only_fields_are_refused(self, api):
        r = post(
            api,
            {**DIRECT, "items": [{"item": 1, "quantity": 1}], "pickup_location": 1},
        )
        assert {"items", "pickup_location"} <= set(r.json()["errors"])

    def test_notes_are_trimmed(self, api):
        o = post(api, {**DIRECT, "description": "  Fragile  "}).json()["data"]["order"]
        assert o["description"] == "Fragile"

    def test_two_orders_get_two_references(self, api):
        a = post(api, DIRECT).json()["data"]["order"]["reference"]
        b = post(api, DIRECT).json()["data"]["order"]["reference"]
        assert a != b


def test_a_failed_create_leaves_nothing_behind(api, open_shop, item):
    body = shop_body(open_shop, item)
    body["delivery"] = {"name": "", "address": ""}
    post(api, body)
    assert Order.objects.count() == 0
    assert OrderStatusChange.objects.count() == 0


def test_the_new_order_is_in_the_clients_list_only(api, open_shop, item, trader, admin):
    pk = post(api, shop_body(open_shop, item)).json()["data"]["order"]["id"]
    assert pk in [o["id"] for o in api.get(reverse(URL)).json()["data"]["results"]]
    # the shop owner sees nothing until review (BR-11)
    assert client_for(trader).get(reverse(URL)).json()["data"]["count"] == 0
    assert client_for(admin).get(reverse(URL)).json()["data"]["count"] == 1
