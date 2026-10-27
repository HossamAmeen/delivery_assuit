import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.locations.models import Location, SavedAddress
from apps.orders import lifecycle
from apps.orders.models import Order, OrderItem, OrderStatusChange
from apps.shops.models import ShopItem

from .conftest import client_for, make_order

pytestmark = pytest.mark.django_db


def edit(c, pk, **body):
    return c.patch(reverse("order-detail", args=[pk]), body, format="json")


@pytest.fixture
def location(trader):
    return Location.objects.create(
        owner=trader, name="Main", address="12 Nile St", is_default_pickup=True
    )


@pytest.fixture
def item(shop):
    return ShopItem.objects.create(shop=shop, name="Cheese pie", price="10.00")


@pytest.fixture
def shop_order(client_user, shop, item, location):
    o = make_order(client_user, shop=shop)
    OrderItem.objects.create(
        order=o, item=item, name="Cheese pie", quantity=1, unit_price="10.00"
    )
    return o


@pytest.fixture
def direct_order(client_user):
    return make_order(client_user, description="Documents")


class TestAccess:
    def test_anonymous_is_401(self, shop_order):
        assert (
            APIClient()
            .patch(reverse("order-detail", args=[shop_order.pk]), {}, format="json")
            .status_code
            == 401
        )

    def test_another_client_gets_404(self, shop_order, client2):
        assert (
            edit(client_for(client2), shop_order.pk, description="Hack").status_code
            == 404
        )
        assert Order.objects.get(pk=shop_order.pk).description == "A box"

    def test_trader_and_driver_cannot_edit(self, shop_order, trader, admin):
        lifecycle.transition(shop_order, "available", admin)
        assert (
            edit(client_for(trader), shop_order.pk, description="Hack").status_code
            == 403
        )

    def test_driver_cannot_edit(self, client_user, driver):
        o = make_order(client_user, status="assigned", driver=driver)
        assert edit(client_for(driver), o.pk, description="Hack").status_code == 403


class TestBoundary:
    """BR-13: allowed before assignment, refused from ASSIGNED on."""

    @pytest.mark.parametrize("status", ["created", "available"])
    def test_client_can_edit_before_assignment(self, status, client_user):
        o = make_order(client_user, status=status)
        r = edit(client_for(client_user), o.pk, description="Fragile box")
        assert (
            r.status_code == 200
            and r.json()["data"]["order"]["description"] == "Fragile box"
        )

    @pytest.mark.parametrize("status", ["assigned", "picked_up", "in_delivery"])
    def test_client_is_refused_from_assignment_on(self, status, client_user, driver):
        o = make_order(client_user, status=status, driver=driver)
        assert (
            edit(client_for(client_user), o.pk, description="Late").status_code == 403
        )
        assert Order.objects.get(pk=o.pk).description == "A box"

    @pytest.mark.parametrize(
        "status", ["assigned", "picked_up", "in_delivery", "delivered", "cancelled"]
    )
    def test_staff_are_refused_too_with_a_clear_status_error(
        self, status, client_user, driver, admin
    ):
        o = make_order(
            client_user, status=status, driver=driver if status != "cancelled" else None
        )
        r = edit(client_for(admin), o.pk, description="Late")
        assert r.status_code == 400 and "status" in r.json()["errors"]

    @pytest.mark.parametrize("status", ["delivered", "cancelled"])
    def test_client_cannot_edit_finished_orders(self, status, client_user, driver):
        o = make_order(
            client_user, status=status, driver=driver if status == "delivered" else None
        )
        assert (
            edit(client_for(client_user), o.pk, description="Late").status_code == 403
        )

    def test_staff_can_edit_before_assignment(self, client_user, manager):
        o = make_order(client_user, status="available")
        assert (
            edit(client_for(manager), o.pk, description="Fixed by staff").status_code
            == 200
        )


class TestReReview:
    def test_editing_an_available_order_sends_it_back_to_review(self, client_user):
        o = make_order(client_user, status="available")
        r = edit(client_for(client_user), o.pk, description="Changed")
        assert r.json()["data"]["order"]["status"] == "created"
        row = OrderStatusChange.objects.filter(order=o).last()
        assert (row.from_status, row.to_status, row.reason, row.actor_id) == (
            "available",
            "created",
            "edited",
            client_user.pk,
        )

    def test_a_created_order_stays_created_without_a_new_history_row(self, client_user):
        o = make_order(client_user, status="created")
        before = OrderStatusChange.objects.filter(order=o).count()
        edit(client_for(client_user), o.pk, description="Changed")
        assert Order.objects.get(pk=o.pk).status == "created"
        assert OrderStatusChange.objects.filter(order=o).count() == before

    def test_it_can_be_reviewed_again(self, client_user, admin):
        o = make_order(client_user, status="available")
        edit(client_for(client_user), o.pk, description="Changed")
        r = client_for(admin).post(
            reverse("order-approve", args=[o.pk]), {}, format="json"
        )
        assert r.json()["data"]["order"]["status"] == "available"


class TestDirectOrder:
    def test_edit_places_and_description(self, direct_order, client_user):
        r = edit(
            client_for(client_user),
            direct_order.pk,
            description="  New details ",
            pickup={"name": "Office", "address": "1 Tahrir Sq"},
            delivery={
                "name": "Mum",
                "address": "9 Rose St",
                "latitude": 30.1,
                "longitude": 31.2,
            },
        )
        o = r.json()["data"]["order"]
        assert o["description"] == "New details"
        assert o["pickup"]["name"] == "Office" and o["delivery"]["latitude"] == 30.1

    def test_only_what_is_sent_changes(self, direct_order, client_user):
        edit(client_for(client_user), direct_order.pk, description="Only this")
        o = Order.objects.get(pk=direct_order.pk)
        assert (o.description, o.delivery_address) == ("Only this", "5 Garden St")

    def test_saved_addresses_are_resolved_for_the_owner_only(
        self, direct_order, client_user, client2
    ):
        mine = SavedAddress.objects.create(
            owner=client_user, name="Home", address="5 Garden St"
        )
        theirs = SavedAddress.objects.create(
            owner=client2, name="Secret", address="secret addr"
        )
        c = client_for(client_user)
        assert (
            edit(c, direct_order.pk, delivery_saved_address=mine.pk).status_code == 200
        )
        r = edit(c, direct_order.pk, pickup_saved_address=theirs.pk)
        assert r.status_code == 400 and "secret" not in r.content.decode()

    @pytest.mark.parametrize("text", ["", "  ", "ab"])
    def test_description_stays_mandatory(self, direct_order, client_user, text):
        r = edit(client_for(client_user), direct_order.pk, description=text)
        assert r.status_code == 400 and "description" in r.json()["errors"]

    def test_shop_only_fields_are_refused(self, direct_order, client_user):
        r = edit(
            client_for(client_user),
            direct_order.pk,
            items=[{"item": 1, "quantity": 1}],
            pickup_location=1,
            shop=1,
        )
        assert {"items", "pickup_location", "shop"} <= set(r.json()["errors"])

    def test_bad_place_and_both_forms_are_refused(self, direct_order, client_user):
        c = client_for(client_user)
        assert (
            edit(c, direct_order.pk, delivery={"name": "", "address": "x"}).status_code
            == 400
        )
        mine = SavedAddress.objects.create(
            owner=client_user, name="Home", address="5 Garden St"
        )
        r = edit(
            c,
            direct_order.pk,
            delivery={"name": "Ok", "address": "ok addr"},
            delivery_saved_address=mine.pk,
        )
        assert r.status_code == 400 and "delivery" in r.json()["errors"]


class TestShopOrder:
    def test_replace_items_and_snapshot_the_current_price(
        self, shop_order, client_user, shop, item
    ):
        item.price = "12.00"
        item.save()
        other = ShopItem.objects.create(shop=shop, name="Falafel")
        r = edit(
            client_for(client_user),
            shop_order.pk,
            items=[{"item": item.pk, "quantity": 2}, {"item": other.pk, "quantity": 1}],
        )
        o = r.json()["data"]["order"]
        assert o["items"] == [
            {"name": "Cheese pie", "quantity": 2, "price": 12},
            {"name": "Falafel", "quantity": 1, "price": None},
        ]
        assert OrderItem.objects.filter(order=shop_order).count() == 2

    def test_a_failed_item_edit_keeps_the_old_lines(
        self, shop_order, client_user, trader2
    ):
        from apps.shops.services import get_or_create_shop

        foreign = ShopItem.objects.create(
            shop=get_or_create_shop(trader2), name="Theirs"
        )
        r = edit(
            client_for(client_user),
            shop_order.pk,
            items=[{"item": foreign.pk, "quantity": 1}],
        )
        assert r.status_code == 400 and "items" in r.json()["errors"]
        assert [l.name for l in OrderItem.objects.filter(order=shop_order)] == [
            "Cheese pie"
        ]

    @pytest.mark.parametrize("items", [[], [{"item": 1, "quantity": 0}]])
    def test_items_cannot_become_empty_or_invalid(self, shop_order, client_user, items):
        r = edit(client_for(client_user), shop_order.pk, items=items)
        assert r.status_code == 400 and "items" in r.json()["errors"]

    def test_change_pickup_location_within_the_shop(
        self, shop_order, client_user, trader, trader2
    ):
        second = Location.objects.create(
            owner=trader, name="Second", address="2 Side St"
        )
        foreign = Location.objects.create(owner=trader2, name="X", address="far away")
        c = client_for(client_user)
        assert (
            edit(c, shop_order.pk, pickup_location=second.pk).json()["data"]["order"][
                "pickup"
            ]["name"]
            == "Second"
        )
        assert (
            "pickup_location"
            in edit(c, shop_order.pk, pickup_location=foreign.pk).json()["errors"]
        )

    def test_the_shop_cannot_change_and_direct_fields_are_refused(
        self, shop_order, client_user
    ):
        r = edit(
            client_for(client_user),
            shop_order.pk,
            shop=999,
            pickup={"name": "A b", "address": "abc"},
        )
        assert {"shop", "pickup"} <= set(r.json()["errors"])

    def test_description_is_optional_on_a_shop_order(self, shop_order, client_user):
        assert (
            edit(client_for(client_user), shop_order.pk, description="").status_code
            == 200
        )

    def test_closed_shop_does_not_block_editing_the_delivery_place(
        self, shop_order, client_user, shop
    ):
        shop.is_available = False
        shop.save()
        r = edit(
            client_for(client_user),
            shop_order.pk,
            delivery={"name": "Home", "address": "6 Garden St"},
        )
        assert r.status_code == 200
