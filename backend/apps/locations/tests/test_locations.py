import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.locations.models import Location
from apps.locations.services import MAX_LOCATIONS

from .conftest import client_for, make_user

pytestmark = pytest.mark.django_db
LIST = "location-list"
BODY = {"name": "Main branch", "address": "12 Nile St, Cairo"}


def post(client, **extra):
    return client.post(reverse(LIST), {**BODY, **extra}, format="json")


def detail(pk):
    return reverse("location-detail", args=[pk])


class TestAccess:
    def test_anonymous_is_401(self):
        assert APIClient().get(reverse(LIST)).status_code == 401

    @pytest.mark.parametrize("role", ["client", "driver", "manager", "admin"])
    def test_other_roles_are_403(self, role):
        c = client_for(make_user(f"u_{role}", role, "01099990001"))
        assert c.get(reverse(LIST)).status_code == 403
        assert c.post(reverse(LIST), BODY, format="json").status_code == 403

    def test_pending_trader_is_403(self):
        t = make_user("pend", "trader", "01099990002", status="pending_approval")
        # A pending account cannot log in, so craft the client from an active one then flip it.
        t.status = "active"
        t.save()
        c = client_for(t)
        t.status = "pending_approval"
        t.save()
        assert c.get(reverse(LIST)).status_code == 403


class TestCreateAndList:
    def test_create_returns_the_location_with_defaults(self, trader_client):
        r = post(trader_client)
        assert r.status_code == 201
        loc = r.json()["data"]["location"]
        assert loc["name"] == "Main branch"
        assert loc["is_pickup"] is True
        assert loc["is_delivery"] is False
        assert loc["latitude"] is None and loc["longitude"] is None

    def test_name_and_address_are_trimmed(self, trader_client):
        r = post(trader_client, name="  Shop  ", address="  Addr here ")
        loc = r.json()["data"]["location"]
        assert (loc["name"], loc["address"]) == ("Shop", "Addr here")

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("name", ""),
            ("name", "a"),
            ("name", "x" * 101),
            ("address", ""),
            ("address", "ab"),
        ],
    )
    def test_bad_name_or_address(self, trader_client, field, value):
        r = post(trader_client, **{field: value})
        assert r.status_code == 400
        assert field in r.json()["errors"]

    def test_missing_name_and_address(self, trader_client):
        r = trader_client.post(reverse(LIST), {}, format="json")
        assert set(r.json()["errors"]) >= {"name", "address"}

    def test_coordinates_round_trip_as_numbers(self, trader_client):
        loc = post(trader_client, latitude=30.0444, longitude=31.2357).json()["data"][
            "location"
        ]
        assert loc["latitude"] == 30.0444
        assert loc["longitude"] == 31.2357

    @pytest.mark.parametrize(
        ("lat", "lng"), [(91, 0), (-91, 0), (0, 181), (0, -181), ("abc", 0)]
    )
    def test_out_of_range_coordinates(self, trader_client, lat, lng):
        r = post(trader_client, latitude=lat, longitude=lng)
        assert r.status_code == 400

    def test_one_coordinate_alone_is_rejected(self, trader_client):
        r = post(trader_client, latitude=30.0)
        assert r.status_code == 400
        assert "longitude" in r.json()["errors"]
        r = post(trader_client, longitude=30.0)
        assert "latitude" in r.json()["errors"]

    def test_list_is_own_only_newest_first_and_paginated(
        self, trader_client, trader2_client
    ):
        a = post(trader_client, name="First").json()["data"]["location"]["id"]
        b = post(trader_client, name="Second").json()["data"]["location"]["id"]
        post(trader2_client, name="Other")
        data = trader_client.get(reverse(LIST)).json()["data"]
        assert data["count"] == 2
        assert [x["id"] for x in data["results"]] == [b, a]

    def test_limit_of_live_locations(self, trader):
        c = client_for(trader)
        Location.objects.bulk_create(
            [
                Location(owner=trader, name=f"L{i}", address="addr x")
                for i in range(MAX_LOCATIONS)
            ]
        )
        r = post(c)
        assert r.status_code == 400
        assert "non_field_errors" in r.json()["errors"]


class TestFlags:
    def test_needs_pickup_or_delivery(self, trader_client):
        r = post(trader_client, is_pickup=False, is_delivery=False)
        assert r.status_code == 400
        assert "is_pickup" in r.json()["errors"]

    def test_delivery_only_is_allowed_and_never_default(self, trader_client):
        loc = post(trader_client, is_pickup=False, is_delivery=True).json()["data"][
            "location"
        ]
        assert loc["is_default_pickup"] is False

    def test_default_needs_pickup(self, trader_client):
        r = post(
            trader_client, is_pickup=False, is_delivery=True, is_default_pickup=True
        )
        assert r.status_code == 400
        assert "is_default_pickup" in r.json()["errors"]

    def test_first_pickup_becomes_default(self, trader_client):
        assert (
            post(trader_client).json()["data"]["location"]["is_default_pickup"] is True
        )
        assert (
            post(trader_client, name="Second").json()["data"]["location"][
                "is_default_pickup"
            ]
            is False
        )

    def test_explicit_default_moves_the_flag(self, trader_client, trader):
        first = post(trader_client).json()["data"]["location"]["id"]
        second = post(trader_client, name="Second", is_default_pickup=True).json()[
            "data"
        ]["location"]["id"]
        defaults = list(
            Location.objects.filter(owner=trader, is_default_pickup=True).values_list(
                "id", flat=True
            )
        )
        assert defaults == [second]
        assert first != second

    def test_patch_default_moves_the_flag(self, trader_client, trader):
        first = post(trader_client).json()["data"]["location"]["id"]
        second = post(trader_client, name="Second").json()["data"]["location"]["id"]
        r = trader_client.patch(
            detail(second), {"is_default_pickup": True}, format="json"
        )
        assert r.status_code == 200
        assert not Location.objects.get(pk=first).is_default_pickup
        assert Location.objects.get(pk=second).is_default_pickup

    def test_turning_pickup_off_promotes_the_next(self, trader_client):
        first = post(trader_client).json()["data"]["location"]["id"]
        second = post(trader_client, name="Second").json()["data"]["location"]["id"]
        r = trader_client.patch(
            detail(first), {"is_pickup": False, "is_delivery": True}, format="json"
        )
        assert r.status_code == 200
        assert r.json()["data"]["location"]["is_default_pickup"] is False
        assert Location.objects.get(pk=second).is_default_pickup

    def test_patch_rejects_turning_both_off(self, trader_client):
        pk = post(trader_client).json()["data"]["location"]["id"]
        r = trader_client.patch(detail(pk), {"is_pickup": False}, format="json")
        assert r.status_code == 400

    def test_flag_changes_do_not_touch_other_traders(
        self, trader_client, trader2_client, trader2
    ):
        post(trader2_client)
        post(trader_client)
        assert (
            Location.objects.filter(owner=trader2, is_default_pickup=True).count() == 1
        )


class TestEditAndDelete:
    def test_patch_partial_and_coordinates_pair_check(self, trader_client):
        pk = post(trader_client, latitude=30, longitude=31).json()["data"]["location"][
            "id"
        ]
        r = trader_client.patch(detail(pk), {"name": "Renamed"}, format="json")
        assert r.json()["data"]["location"]["name"] == "Renamed"
        r = trader_client.patch(detail(pk), {"latitude": None}, format="json")
        assert r.status_code == 400
        r = trader_client.patch(
            detail(pk), {"latitude": None, "longitude": None}, format="json"
        )
        assert r.status_code == 200

    def test_delete_is_soft_and_hides_the_row(self, trader_client):
        pk = post(trader_client).json()["data"]["location"]["id"]
        assert trader_client.delete(detail(pk)).status_code == 200
        assert trader_client.get(detail(pk)).status_code == 404
        assert Location.all_objects.get(pk=pk).deleted_at is not None
        assert trader_client.get(reverse(LIST)).json()["data"]["count"] == 0

    def test_deleting_the_default_promotes_the_oldest_pickup(self, trader_client):
        first = post(trader_client).json()["data"]["location"]["id"]
        second = post(trader_client, name="Second").json()["data"]["location"]["id"]
        post(trader_client, name="Third")
        trader_client.delete(detail(first))
        assert Location.objects.get(pk=second).is_default_pickup

    def test_deleted_default_does_not_block_a_new_default(self, trader_client, trader):
        first = post(trader_client).json()["data"]["location"]["id"]
        trader_client.delete(detail(first))
        post(trader_client, name="New")
        assert (
            Location.objects.filter(owner=trader, is_default_pickup=True).count() == 1
        )


class TestOwnership:
    def test_another_traders_row_is_404_for_every_method(
        self, trader_client, trader2_client
    ):
        pk = post(trader2_client).json()["data"]["location"]["id"]
        assert trader_client.get(detail(pk)).status_code == 404
        assert (
            trader_client.patch(detail(pk), {"name": "Hack"}, format="json").status_code
            == 404
        )
        assert trader_client.delete(detail(pk)).status_code == 404
        assert Location.objects.get(pk=pk).name == "Main branch"

    def test_unknown_id_is_404(self, trader_client):
        assert trader_client.get(detail(9999)).status_code == 404

    def test_owner_cannot_be_set_from_the_body(self, trader_client, trader2):
        r = post(trader_client, owner=trader2.pk, id=99)
        loc = r.json()["data"]["location"]
        assert Location.objects.get(pk=loc["id"]).owner.username == "trader1"
        assert loc["id"] != 99


class TestArabic:
    def test_validation_message_follows_accept_language(self, trader_client):
        r = trader_client.post(
            reverse(LIST),
            {**BODY, "is_pickup": False, "is_delivery": False},
            format="json",
            HTTP_ACCEPT_LANGUAGE="ar",
        )
        assert r.json()["errors"]["is_pickup"][0] != "Choose pickup, delivery, or both."
