import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.shops import services
from apps.shops.models import ShopItem

from .conftest import client_for, make_user

pytestmark = pytest.mark.django_db
LIST = "shop-item-list"


def post(client, **extra):
    return client.post(reverse(LIST), {"name": "Cheese pie", **extra}, format="json")


def detail(pk):
    return reverse("shop-item-detail", args=[pk])


def item_id(response):
    return response.json()["data"]["item"]["id"]


class TestAccess:
    def test_anonymous_is_401(self):
        assert APIClient().get(reverse(LIST)).status_code == 401

    @pytest.mark.parametrize("role", ["client", "driver", "manager", "admin"])
    def test_other_roles_are_403(self, role):
        c = client_for(make_user(f"u_{role}", role, "01099990001"))
        assert c.get(reverse(LIST)).status_code == 403
        assert post(c).status_code == 403


class TestCreateAndList:
    def test_create_defaults(self, trader_client):
        item = post(trader_client).json()["data"]["item"]
        assert item["name"] == "Cheese pie"
        assert item["description"] == ""
        assert item["is_hidden"] is False
        assert item["price"] is None

    def test_price_in_the_body_is_ignored(self, trader_client):
        r = post(trader_client, price=50)
        assert r.json()["data"]["item"]["price"] is None
        pk = item_id(r)
        r = trader_client.patch(detail(pk), {"price": 10}, format="json")
        assert r.json()["data"]["item"]["price"] is None
        assert ShopItem.objects.get(pk=pk).price is None

    @pytest.mark.parametrize("name", ["", "a", "x" * 101, "   "])
    def test_bad_name(self, trader_client, name):
        r = post(trader_client, name=name)
        assert r.status_code == 400
        assert "name" in r.json()["errors"]

    def test_description_limit(self, trader_client):
        assert post(trader_client, description="x" * 301).status_code == 400

    def test_list_is_own_only_paginated_newest_first(
        self, trader_client, trader2_client
    ):
        a = item_id(post(trader_client, name="Alpha"))
        b = item_id(post(trader_client, name="Bravo"))
        post(trader2_client, name="Other shop")
        data = trader_client.get(reverse(LIST)).json()["data"]
        assert data["count"] == 2
        assert [x["id"] for x in data["results"]] == [b, a]

    def test_filters(self, trader_client):
        post(trader_client, name="Cheese pie")
        pk = item_id(post(trader_client, name="Chicken wrap"))
        trader_client.patch(detail(pk), {"is_hidden": True}, format="json")
        names = lambda q: [
            x["name"]
            for x in trader_client.get(reverse(LIST) + q).json()["data"]["results"]
        ]
        assert names("?hidden=true") == ["Chicken wrap"]
        assert names("?hidden=false") == ["Cheese pie"]
        assert sorted(names("?search=ch")) == ["Cheese pie", "Chicken wrap"]
        assert names("?search=wrap") == ["Chicken wrap"]

    def test_limit(self, trader_client, trader):
        shop = services.get_or_create_shop(trader)
        ShopItem.objects.bulk_create(
            [ShopItem(shop=shop, name=f"Item {i}") for i in range(services.MAX_ITEMS)]
        )
        r = post(trader_client, name="One more")
        assert r.status_code == 400
        assert "non_field_errors" in r.json()["errors"]


class TestDuplicates:
    def test_duplicate_name_is_case_insensitive(self, trader_client):
        post(trader_client, name="Cheese pie")
        r = post(trader_client, name="CHEESE PIE")
        assert r.status_code == 400
        assert "name" in r.json()["errors"]

    def test_other_shops_may_use_the_same_name(self, trader_client, trader2_client):
        post(trader_client)
        assert post(trader2_client).status_code == 201

    def test_deleted_name_can_be_reused(self, trader_client):
        pk = item_id(post(trader_client))
        trader_client.delete(detail(pk))
        assert post(trader_client).status_code == 201

    def test_rename_to_an_existing_name_is_rejected_but_own_name_is_fine(
        self, trader_client
    ):
        post(trader_client, name="Alpha")
        pk = item_id(post(trader_client, name="Bravo"))
        assert (
            trader_client.patch(
                detail(pk), {"name": "alpha"}, format="json"
            ).status_code
            == 400
        )
        assert (
            trader_client.patch(
                detail(pk), {"name": "Bravo"}, format="json"
            ).status_code
            == 200
        )

    def test_database_constraint_backs_the_check(self, trader):
        shop = services.get_or_create_shop(trader)
        services.create_item(shop, name="Alpha")
        with pytest.raises(Exception) as err:
            services.create_item(shop, name="alpha")
        assert "name" in getattr(err.value, "detail", {})


class TestEditHideDelete:
    def test_edit_and_hide_and_unhide(self, trader_client):
        pk = item_id(post(trader_client))
        r = trader_client.patch(
            detail(pk),
            {"name": "Renamed", "description": "Warm", "is_hidden": True},
            format="json",
        )
        item = r.json()["data"]["item"]
        assert (item["name"], item["description"], item["is_hidden"]) == (
            "Renamed",
            "Warm",
            True,
        )
        assert trader_client.get(reverse(LIST)).json()["data"]["count"] == 1
        r = trader_client.patch(detail(pk), {"is_hidden": False}, format="json")
        assert r.json()["data"]["item"]["is_hidden"] is False

    def test_delete_is_soft(self, trader_client):
        pk = item_id(post(trader_client))
        assert trader_client.delete(detail(pk)).status_code == 200
        assert trader_client.get(detail(pk)).status_code == 404
        assert ShopItem.all_objects.get(pk=pk).deleted_at is not None


class TestOwnership:
    def test_another_shops_item_is_404_for_every_method(
        self, trader_client, trader2_client
    ):
        pk = item_id(post(trader2_client))
        assert trader_client.get(detail(pk)).status_code == 404
        assert (
            trader_client.patch(detail(pk), {"name": "Hack"}, format="json").status_code
            == 404
        )
        assert trader_client.delete(detail(pk)).status_code == 404
        assert ShopItem.objects.get(pk=pk).name == "Cheese pie"

    def test_shop_cannot_be_set_from_the_body(
        self, trader_client, trader2_client, trader2
    ):
        from apps.shops.services import get_or_create_shop

        other = get_or_create_shop(trader2)
        pk = item_id(post(trader_client, shop=other.pk))
        assert ShopItem.objects.get(pk=pk).shop_id != other.pk

    def test_first_item_call_creates_the_shop(self, trader_client, trader):
        post(trader_client)
        assert trader.shop.items.count() == 1
