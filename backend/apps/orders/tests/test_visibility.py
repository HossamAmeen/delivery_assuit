import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.orders import lifecycle
from apps.orders.models import OrderItem, OrderStatusChange

from .conftest import client_for, make_order, make_user

pytestmark = pytest.mark.django_db
LIST = "order-list"


def ids(response):
    return {o["id"] for o in response.json()["data"]["results"]}


def detail(pk):
    return reverse("order-detail", args=[pk])


@pytest.fixture
def world(admin, client_user, client2, trader, trader2, driver, driver2, shop):
    from apps.shops.services import get_or_create_shop

    other_shop = get_or_create_shop(trader2)
    mine_created = make_order(client_user, shop=shop)
    mine_available = make_order(client_user, shop=shop, status="available")
    lifecycle.record_creation(mine_available, client_user)
    assigned = make_order(client_user, shop=shop, status="assigned", driver=driver)
    # a real assigned order went through review
    OrderStatusChange.objects.create(
        order=assigned, from_status="created", to_status="available", actor=admin
    )
    theirs = make_order(client2, shop=other_shop, status="available")
    theirs_assigned = make_order(client2, status="assigned", driver=driver2)
    # an order approved and then cancelled still counts as approved
    approved_then_cancelled = make_order(client_user, shop=shop)
    lifecycle.transition(approved_then_cancelled, "available", admin)
    lifecycle.transition(approved_then_cancelled, "cancelled", admin, reason="no")
    # an order rejected at review was never approved
    rejected = make_order(client_user, shop=shop)
    lifecycle.transition(rejected, "cancelled", admin, reason="bad")
    return {
        "mine_created": mine_created,
        "mine_available": mine_available,
        "assigned": assigned,
        "theirs": theirs,
        "theirs_assigned": theirs_assigned,
        "approved_then_cancelled": approved_then_cancelled,
        "rejected": rejected,
    }


def as_user(user):
    return client_for(user)


class TestAccess:
    def test_anonymous_is_401(self):
        assert APIClient().get(reverse(LIST)).status_code == 401

    def test_inactive_account_is_403(self, client_user):
        c = client_for(client_user)
        client_user.status = "deactivated"
        client_user.save()
        assert c.get(reverse(LIST)).status_code == 403


class TestScopes:
    def test_client_sees_only_own_orders(self, world, client_user):
        c = as_user(client_user)
        got = ids(c.get(reverse(LIST)))
        assert got == {
            world[k].pk
            for k in (
                "mine_created",
                "mine_available",
                "assigned",
                "approved_then_cancelled",
                "rejected",
            )
        }

    def test_other_client_sees_none_of_them(self, world, client2):
        c = as_user(client2)
        got = ids(c.get(reverse(LIST)))
        assert got == {world["theirs"].pk, world["theirs_assigned"].pk}
        for key in ("mine_created", "assigned", "rejected"):
            assert c.get(detail(world[key].pk)).status_code == 404

    def test_trader_sees_only_approved_orders_to_their_shop(self, world, trader):
        c = as_user(trader)
        got = ids(c.get(reverse(LIST)))
        assert got == {
            world["mine_available"].pk,
            world["assigned"].pk,
            world["approved_then_cancelled"].pk,
        }
        # not yet reviewed, rejected at review, another shop, a direct order
        for key in ("mine_created", "rejected", "theirs", "theirs_assigned"):
            assert c.get(detail(world[key].pk)).status_code == 404

    def test_driver_sees_only_orders_assigned_to_them(self, world, driver):
        c = as_user(driver)
        assert ids(c.get(reverse(LIST))) == {world["assigned"].pk}
        assert c.get(detail(world["assigned"].pk)).status_code == 200
        for key in ("mine_available", "theirs_assigned", "mine_created"):
            assert c.get(detail(world[key].pk)).status_code == 404

    @pytest.mark.parametrize("who", ["admin", "manager"])
    def test_staff_see_everything(self, world, who, request):
        c = as_user(request.getfixturevalue(who))
        assert ids(c.get(reverse(LIST))) == {o.pk for o in world.values()}
        assert c.get(detail(world["theirs"].pk)).status_code == 200

    def test_unknown_id_is_404(self, admin):
        assert as_user(admin).get(detail(9999)).status_code == 404


class TestPayload:
    def test_phone_only_for_staff(self, order, admin, client_user, trader):
        lifecycle.transition(order, "available", admin)
        staff = as_user(admin).get(detail(order.pk)).json()["data"]["order"]
        assert staff["client"]["phone"] == client_user.phone
        for user in (client_user, trader):
            data = as_user(user).get(detail(order.pk)).json()["data"]["order"]
            assert "phone" not in data["client"]

    def test_driver_gets_contacts_while_the_order_is_active(
        self, order, driver, client_user
    ):
        order.driver = driver
        order.status = "assigned"
        order.save()
        data = as_user(driver).get(detail(order.pk)).json()["data"]["order"]
        assert data["client"]["phone"] == client_user.phone
        assert "phone" in data["shop"]
        assert data["driver"] == {"id": driver.pk, "full_name": driver.full_name}

    def test_shape(self, order, client_user):
        data = as_user(client_user).get(detail(order.pk)).json()["data"]["order"]
        assert data["reference"] == f"ORD-{order.pk:06d}"
        assert data["status"] == "created"
        assert data["shop"]["name"] == order.shop.name
        assert data["driver"] is None
        assert data["pickup"] == {
            "name": "Main branch",
            "address": "12 Nile St",
            "latitude": None,
            "longitude": None,
        }
        assert data["items"] == [{"name": "Cheese pie", "quantity": 2, "price": None}]
        assert data["delivery_fee"] is None
        assert data["cancel_reason"] == ""

    def test_direct_order_has_no_shop(self, client_user):
        o = make_order(client_user)
        data = as_user(client_user).get(detail(o.pk)).json()["data"]["order"]
        assert data["shop"] is None

    def test_coordinates_and_fee_are_numbers(self, client_user):
        o = make_order(
            client_user,
            pickup_latitude="30.044400",
            pickup_longitude="31.235700",
            delivery_fee="25.50",
        )
        data = as_user(client_user).get(detail(o.pk)).json()["data"]["order"]
        assert data["pickup"]["latitude"] == 30.0444
        assert data["delivery_fee"] == 25.5

    def test_cancel_reason_is_visible_to_the_client(self, order, admin, client_user):
        lifecycle.transition(order, "cancelled", admin, reason="Address unclear")
        data = as_user(client_user).get(detail(order.pk)).json()["data"]["order"]
        assert data["status"] == "cancelled"
        assert data["cancel_reason"] == "Address unclear"


class TestFilterAndPaging:
    def test_status_filter_and_order(self, world, admin):
        c = as_user(admin)
        r = c.get(reverse(LIST), {"status": "available"})
        assert ids(r) == {world["mine_available"].pk, world["theirs"].pk}
        r = c.get(reverse(LIST))
        rows = r.json()["data"]["results"]
        assert [o["id"] for o in rows] == sorted((o["id"] for o in rows), reverse=True)
        assert c.get(reverse(LIST), {"status": "bogus"}).status_code == 400

    def test_list_is_paginated(self, client_user):
        for _ in range(3):
            make_order(client_user)
        data = as_user(client_user).get(reverse(LIST), {"page_size": 2}).json()["data"]
        assert data["count"] == 3
        assert len(data["results"]) == 2
        assert data["next"]


def test_a_new_user_with_no_orders_gets_an_empty_list(client2):
    data = as_user(client2).get(reverse(LIST)).json()["data"]
    assert data["count"] == 0


def test_items_are_returned_in_the_list_too(order, client_user):
    OrderItem.objects.create(order=order, name="Falafel", quantity=1)
    rows = as_user(client_user).get(reverse(LIST)).json()["data"]["results"]
    assert [i["name"] for i in rows[0]["items"]] == ["Cheese pie", "Falafel"]


def test_helper_users_exist():
    assert make_user  # imported for the shared fixtures
