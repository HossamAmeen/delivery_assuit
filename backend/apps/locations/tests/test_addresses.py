import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.locations.models import SavedAddress
from apps.locations.services import MAX_ADDRESSES

from .conftest import client_for, make_user

pytestmark = pytest.mark.django_db
LIST = "address-list"
BODY = {"name": "Home", "address": "5 Garden St, Giza"}


@pytest.fixture
def client_api(client_user):
    return client_for(client_user)


@pytest.fixture
def client2_api(db):
    return client_for(make_user("client2", "client", "01000000021"))


def post(c, **extra):
    return c.post(reverse(LIST), {**BODY, **extra}, format="json")


def detail(pk):
    return reverse("address-detail", args=[pk])


def pk_of(r):
    return r.json()["data"]["address"]["id"]


class TestAccess:
    def test_anonymous_is_401(self):
        assert APIClient().get(reverse(LIST)).status_code == 401

    @pytest.mark.parametrize("role", ["trader", "driver", "manager", "admin"])
    def test_other_roles_are_403(self, role):
        c = client_for(make_user(f"u_{role}", role, "01099990001"))
        assert c.get(reverse(LIST)).status_code == 403
        assert post(c).status_code == 403


class TestCrud:
    def test_create_returns_place_fields_only(self, client_api):
        a = post(client_api, latitude=30.05, longitude=31.23).json()["data"]["address"]
        assert set(a) == {
            "id",
            "name",
            "address",
            "latitude",
            "longitude",
            "created_at",
        }
        assert (a["latitude"], a["longitude"]) == (30.05, 31.23)

    def test_no_pickup_or_delivery_flags_are_stored(self, client_api, client_user):
        post(client_api, is_pickup=False, is_default_pickup=True)
        assert not hasattr(SavedAddress.objects.get(owner=client_user), "is_pickup")

    @pytest.mark.parametrize(
        ("field", "value"),
        [("name", ""), ("name", "a"), ("address", ""), ("address", "ab")],
    )
    def test_bad_input(self, client_api, field, value):
        r = post(client_api, **{field: value})
        assert r.status_code == 400
        assert field in r.json()["errors"]

    def test_coordinates_validated_as_a_pair_and_in_range(self, client_api):
        assert post(client_api, latitude=30).status_code == 400
        assert post(client_api, latitude=95, longitude=10).status_code == 400
        assert post(client_api, latitude=10, longitude=-200).status_code == 400

    def test_list_is_own_only_newest_first(self, client_api, client2_api):
        a = pk_of(post(client_api, name="First"))
        b = pk_of(post(client_api, name="Second"))
        post(client2_api, name="Other")
        data = client_api.get(reverse(LIST)).json()["data"]
        assert data["count"] == 2
        assert [x["id"] for x in data["results"]] == [b, a]

    def test_edit_and_delete(self, client_api):
        pk = pk_of(post(client_api))
        r = client_api.patch(detail(pk), {"name": "Work"}, format="json")
        assert r.json()["data"]["address"]["name"] == "Work"
        assert client_api.delete(detail(pk)).status_code == 200
        assert client_api.get(detail(pk)).status_code == 404
        assert SavedAddress.all_objects.get(pk=pk).deleted_at is not None

    def test_limit(self, client_api, client_user):
        SavedAddress.objects.bulk_create(
            [
                SavedAddress(owner=client_user, name=f"A{i}", address="addr here")
                for i in range(MAX_ADDRESSES)
            ]
        )
        r = post(client_api)
        assert r.status_code == 400
        assert "non_field_errors" in r.json()["errors"]

    def test_deleted_addresses_do_not_count_towards_the_limit(
        self, client_api, client_user
    ):
        SavedAddress.objects.bulk_create(
            [
                SavedAddress(owner=client_user, name=f"A{i}", address="addr here")
                for i in range(MAX_ADDRESSES)
            ]
        )
        SavedAddress.objects.filter(owner=client_user).first().soft_delete()
        assert post(client_api).status_code == 201


class TestOwnership:
    def test_another_clients_row_is_404_for_every_method(self, client_api, client2_api):
        pk = pk_of(post(client2_api))
        assert client_api.get(detail(pk)).status_code == 404
        assert (
            client_api.patch(detail(pk), {"name": "Hack"}, format="json").status_code
            == 404
        )
        assert client_api.delete(detail(pk)).status_code == 404
        assert SavedAddress.objects.get(pk=pk).name == "Home"

    def test_owner_cannot_be_set_from_the_body(self, client_api, client2_api):
        other = make_user("client3", "client", "01000000022")
        pk = pk_of(post(client_api, owner=other.pk))
        assert SavedAddress.objects.get(pk=pk).owner.username == "client1"
