import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.locations.models import Location
from apps.shops.models import ShopItem

from .conftest import client_for, make_order, make_user

pytestmark = pytest.mark.django_db
KINDS = ("driver", "trader", "client")


def rows(r):
    return r.json()["data"]["results"]


class TestAccess:
    @pytest.mark.parametrize("kind", KINDS)
    def test_anonymous_is_401(self, kind):
        assert APIClient().get(reverse(f"staff-{kind}-list")).status_code == 401

    @pytest.mark.parametrize("kind", KINDS)
    @pytest.mark.parametrize("role", ["client", "trader", "driver"])
    def test_other_roles_are_403(self, kind, role):
        c = client_for(make_user(f"u_{role}", role, "01099990001"))
        assert c.get(reverse(f"staff-{kind}-list")).status_code == 403
        assert c.get(reverse(f"staff-{kind}-detail", args=[1])).status_code == 403

    @pytest.mark.parametrize("who", ["admin", "manager"])
    def test_staff_get_in(self, who, request):
        c = client_for(request.getfixturevalue(who))
        for kind in KINDS:
            assert c.get(reverse(f"staff-{kind}-list")).status_code == 200


class TestDrivers:
    def test_lists_every_status_with_delivered_counts_and_only_drivers(
        self, admin, driver, driver2, client_user, trader
    ):
        make_order(client_user, status="delivered", driver=driver)
        make_order(client_user, status="delivered", driver=driver)
        make_order(client_user, status="cancelled", driver=driver)
        pending = make_user("d_p", "driver", "01099990101", status="pending_approval")
        out = rows(client_for(admin).get(reverse("staff-driver-list")))
        by = {r["id"]: r for r in out}
        assert set(by) == {driver.pk, driver2.pk, pending.pk}
        assert by[driver.pk]["delivered_orders"] == 2
        assert by[driver2.pk]["delivered_orders"] == 0
        assert by[pending.pk]["status"] == "pending_approval"
        assert set(by[driver.pk]) == {
            "id",
            "full_name",
            "phone",
            "status",
            "delivered_orders",
        }

    def test_search_and_status_filter(self, manager, driver, driver2):
        driver.full_name = "Omar Hassan"
        driver.save()
        c = client_for(manager)
        assert [
            r["id"]
            for r in rows(c.get(reverse("staff-driver-list"), {"search": "hassan"}))
        ] == [driver.pk]
        assert [
            r["id"]
            for r in rows(
                c.get(reverse("staff-driver-list"), {"search": driver2.phone})
            )
        ] == [driver2.pk]
        driver2.status = "deactivated"
        driver2.save()
        assert [
            r["id"]
            for r in rows(
                c.get(reverse("staff-driver-list"), {"status": "deactivated"})
            )
        ] == [driver2.pk]
        assert (
            c.get(reverse("staff-driver-list"), {"status": "bogus"}).status_code == 400
        )

    def test_a_username_like_search_does_not_match_phones(self, admin, driver):
        # "driver1" contains digits but is not phone-like
        assert (
            rows(
                client_for(admin).get(reverse("staff-driver-list"), {"search": "zzz1"})
            )
            == []
        )

    def test_detail_has_profile_orders_and_performance(
        self, admin, driver, client_user
    ):
        done = make_order(client_user, status="delivered", driver=driver)
        make_order(client_user, status="cancelled", driver=driver)
        active = make_order(client_user, status="in_delivery", driver=driver)
        d = (
            client_for(admin)
            .get(reverse("staff-driver-detail", args=[driver.pk]))
            .json()["data"]
        )
        assert d["user"]["id"] == driver.pk and d["user"]["role"] == "driver"
        assert (d["delivered_orders"], d["cancelled_orders"]) == (1, 1)
        assert d["active_order_reference"] == active.reference
        assert d["orders_total"] == 3
        assert d["recent_orders"][0]["id"] == active.pk and done.pk in [
            o["id"] for o in d["recent_orders"]
        ]
        assert d["recent_orders"][0]["client"]["phone"] == client_user.phone

    def test_detail_of_a_non_driver_or_unknown_id_is_404(self, admin, client_user):
        c = client_for(admin)
        assert (
            c.get(reverse("staff-driver-detail", args=[client_user.pk])).status_code
            == 404
        )
        assert c.get(reverse("staff-driver-detail", args=[9999])).status_code == 404

    def test_deleted_drivers_are_hidden(self, admin, driver):
        driver.soft_delete()
        assert rows(client_for(admin).get(reverse("staff-driver-list"))) == []
        assert (
            client_for(admin)
            .get(reverse("staff-driver-detail", args=[driver.pk]))
            .status_code
            == 404
        )

    def test_recent_orders_are_capped(self, admin, driver, client_user):
        for _ in range(23):
            make_order(client_user, status="delivered", driver=driver)
        d = (
            client_for(admin)
            .get(reverse("staff-driver-detail", args=[driver.pk]))
            .json()["data"]
        )
        assert d["orders_total"] == 23 and len(d["recent_orders"]) == 20


class TestTraders:
    def test_row_has_shop_info_and_order_count(self, admin, trader, shop, client_user):
        shop.name, shop.phone = "Alpha Grill", "01005550000"
        shop.save()
        make_order(client_user, shop=shop)
        make_order(client_user, shop=shop, status="available")
        pending = make_user("t_p", "trader", "01099990201", status="pending_approval")
        out = {
            r["id"]: r
            for r in rows(client_for(admin).get(reverse("staff-trader-list")))
        }
        assert out[trader.pk]["shop_name"] == "Alpha Grill"
        assert out[trader.pk]["shop_phone"] == "01005550000"
        assert out[trader.pk]["orders"] == 2
        assert (
            out[pending.pk] | {}
            and out[pending.pk]["shop_name"] == ""
            and out[pending.pk]["orders"] == 0
        )
        assert out[pending.pk]["status"] == "pending_approval"

    def test_search_by_name_or_phone_and_status(self, manager, trader, trader2):
        c = client_for(manager)
        assert [
            r["id"]
            for r in rows(
                c.get(reverse("staff-trader-list"), {"search": trader.full_name})
            )
        ] == [trader.pk]
        trader2.status = "deactivated"
        trader2.save()
        assert [
            r["id"]
            for r in rows(
                c.get(reverse("staff-trader-list"), {"status": "deactivated"})
            )
        ] == [trader2.pk]

    def test_detail_has_shop_locations_items_and_orders(
        self, admin, trader, shop, client_user
    ):
        Location.objects.create(owner=trader, name="Main", address="12 Nile St")
        ShopItem.objects.create(shop=shop, name="Pie", price="9.50")
        ShopItem.objects.create(shop=shop, name="Hidden", is_hidden=True)
        o = make_order(client_user, shop=shop)
        d = (
            client_for(admin)
            .get(reverse("staff-trader-detail", args=[trader.pk]))
            .json()["data"]
        )
        assert d["shop"]["name"] == shop.name
        assert [x["name"] for x in d["locations"]] == ["Main"]
        assert {i["name"]: i["price"] for i in d["items"]} == {
            "Pie": 9.5,
            "Hidden": None,
        }
        assert [x["id"] for x in d["recent_orders"]] == [o.pk]

    def test_detail_without_a_shop_yet(self, admin):
        t = make_user("t_new", "trader", "01099990202")
        d = (
            client_for(admin)
            .get(reverse("staff-trader-detail", args=[t.pk]))
            .json()["data"]
        )
        assert d["shop"] is None and d["items"] == [] and d["locations"] == []

    def test_other_traders_data_is_not_mixed_in(self, admin, trader, trader2, shop):
        from apps.shops.services import get_or_create_shop

        ShopItem.objects.create(shop=get_or_create_shop(trader2), name="Theirs")
        d = (
            client_for(admin)
            .get(reverse("staff-trader-detail", args=[trader.pk]))
            .json()["data"]
        )
        assert d["items"] == []


class TestClients:
    def test_row_counts_orders_and_detail_lists_them(self, admin, client_user, client2):
        make_order(client_user)
        o = make_order(client_user, status="delivered", driver=None)
        make_order(client2)
        out = {
            r["id"]: r
            for r in rows(client_for(admin).get(reverse("staff-client-list")))
        }
        assert out[client_user.pk]["orders"] == 2 and out[client2.pk]["orders"] == 1
        d = (
            client_for(admin)
            .get(reverse("staff-client-detail", args=[client_user.pk]))
            .json()["data"]
        )
        assert d["orders_total"] == 2 and o.pk in [x["id"] for x in d["recent_orders"]]
        assert d["user"]["status"] == "active"

    def test_search_by_name_and_phone(self, manager, client_user, client2):
        c = client_for(manager)
        assert [
            r["id"]
            for r in rows(
                c.get(reverse("staff-client-list"), {"search": client2.phone})
            )
        ] == [client2.pk]

    def test_only_clients_are_listed(self, admin, client_user, driver, trader):
        assert {
            r["id"] for r in rows(client_for(admin).get(reverse("staff-client-list")))
        } == {client_user.pk}


def test_lists_are_paginated(admin, client_user):
    for i in range(3):
        make_user(f"cc{i}", "client", f"0109999030{i}")
    data = (
        client_for(admin)
        .get(reverse("staff-client-list"), {"page_size": 2})
        .json()["data"]
    )
    assert data["count"] == 4 and len(data["results"]) == 2 and data["next"]
