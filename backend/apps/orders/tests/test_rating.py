import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.orders.models import OrderRating

from .conftest import client_for, make_order, make_user

pytestmark = pytest.mark.django_db


def rate(c, pk, **body):
    return c.post(reverse("order-rating", args=[pk]), body, format="json")


@pytest.fixture
def delivered(client_user, shop, driver):
    return make_order(client_user, shop=shop, status="delivered", driver=driver)


class TestRules:
    def test_anonymous_is_401(self, delivered):
        assert (
            APIClient()
            .post(
                reverse("order-rating", args=[delivered.pk]),
                {"score": 5},
                format="json",
            )
            .status_code
            == 401
        )

    def test_client_rates_once_with_an_optional_comment(
        self, delivered, client_user, driver
    ):
        r = rate(client_for(client_user), delivered.pk, score=5, comment="  Great  ")
        assert r.status_code == 201
        assert r.json()["data"]["order"]["rating"]["score"] == 5
        obj = OrderRating.objects.get(order=delivered)
        assert (obj.client_id, obj.driver_id, obj.comment) == (
            client_user.pk,
            driver.pk,
            "Great",
        )

    def test_comment_is_optional(self, delivered, client_user):
        assert rate(client_for(client_user), delivered.pk, score=3).status_code == 201

    def test_second_rating_is_refused_and_the_first_stays(self, delivered, client_user):
        c = client_for(client_user)
        rate(c, delivered.pk, score=4)
        r = rate(c, delivered.pk, score=1)
        assert r.status_code == 400 and "status" in r.json()["errors"]
        assert OrderRating.objects.get(order=delivered).score == 4

    @pytest.mark.parametrize("score", [0, 6, -1, "x", 3.5, None])
    def test_score_is_1_to_5(self, delivered, client_user, score):
        body = {} if score is None else {"score": score}
        r = rate(client_for(client_user), delivered.pk, **body)
        assert r.status_code == 400 and "score" in r.json()["errors"]
        assert OrderRating.objects.count() == 0

    def test_comment_is_length_limited(self, delivered, client_user):
        assert (
            "comment"
            in rate(
                client_for(client_user), delivered.pk, score=5, comment="x" * 501
            ).json()["errors"]
        )

    @pytest.mark.parametrize(
        "status",
        ["created", "available", "assigned", "picked_up", "in_delivery", "cancelled"],
    )
    def test_only_delivered_orders(self, status, client_user, driver):
        o = make_order(
            client_user,
            status=status,
            driver=driver
            if status in ("assigned", "picked_up", "in_delivery")
            else None,
        )
        r = rate(client_for(client_user), o.pk, score=5)
        assert r.status_code == 400 and "status" in r.json()["errors"]

    def test_another_client_gets_404(self, delivered, client2):
        assert rate(client_for(client2), delivered.pk, score=5).status_code == 404
        assert OrderRating.objects.count() == 0

    @pytest.mark.parametrize("role", ["driver", "trader", "admin", "manager"])
    def test_other_roles_are_403(self, role, delivered, driver, trader, admin, manager):
        user = {"driver": driver, "trader": trader, "admin": admin, "manager": manager}[
            role
        ]
        assert rate(client_for(user), delivered.pk, score=5).status_code == 403
        assert OrderRating.objects.count() == 0


class TestVisibility:
    def test_owner_and_staff_see_it_but_not_driver_or_trader(
        self, delivered, client_user, admin, driver, trader
    ):
        rate(client_for(client_user), delivered.pk, score=4, comment="Nice")
        url = reverse("order-detail", args=[delivered.pk])
        for user in (client_user, admin):
            got = client_for(user).get(url).json()["data"]["order"]["rating"]
            assert got["score"] == 4 and got["comment"] == "Nice"
        for user in (driver,):
            assert client_for(user).get(url).json()["data"]["order"]["rating"] is None

    def test_trader_never_sees_the_rating(self, delivered, client_user, trader, admin):
        from apps.orders.models import OrderStatusChange

        OrderStatusChange.objects.create(
            order=delivered, from_status="created", to_status="available", actor=admin
        )
        rate(client_for(client_user), delivered.pk, score=2, comment="Late")
        data = (
            client_for(trader)
            .get(reverse("order-detail", args=[delivered.pk]))
            .json()["data"]["order"]
        )
        assert data["rating"] is None
        assert (
            "Late" not in client_for(trader).get(reverse("order-list")).content.decode()
        )

    def test_unrated_orders_have_null_rating(self, delivered, client_user):
        assert (
            client_for(client_user)
            .get(reverse("order-detail", args=[delivered.pk]))
            .json()["data"]["order"]["rating"]
            is None
        )


def test_make_user_import():
    assert make_user
