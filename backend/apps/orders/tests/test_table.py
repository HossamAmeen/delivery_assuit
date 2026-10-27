import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.orders import lifecycle
from apps.orders.models import Order

from .conftest import client_for, make_order

pytestmark = pytest.mark.django_db
LIST = "order-list"


def ids(r):
    return {o["id"] for o in r.json()["data"]["results"]}


@pytest.fixture
def dated(client_user, client2):
    """Three orders created on known days, two clients."""
    now = timezone.now()
    out = []
    for days, owner in ((10, client_user), (5, client2), (1, client_user)):
        o = make_order(owner)
        Order.objects.filter(pk=o.pk).update(
            created_at=now - datetime.timedelta(days=days)
        )
        out.append(o)
    return out


def day(n):
    return (timezone.now() - datetime.timedelta(days=n)).date().isoformat()


class TestFilters:
    def test_period_is_inclusive_and_staff_see_all_clients(self, dated, admin):
        c = client_for(admin)
        old, mid, new = dated
        assert ids(c.get(reverse(LIST), {"created_from": day(6)})) == {mid.pk, new.pk}
        assert ids(c.get(reverse(LIST), {"created_to": day(5)})) == {old.pk, mid.pk}
        assert ids(
            c.get(reverse(LIST), {"created_from": day(5), "created_to": day(5)})
        ) == {mid.pk}

    def test_search_by_reference_is_case_insensitive_and_partial(self, dated, admin):
        c = client_for(admin)
        old = dated[0]
        assert ids(c.get(reverse(LIST), {"search": old.reference.lower()})) == {old.pk}
        assert ids(c.get(reverse(LIST), {"search": "ORD-"})) == {o.pk for o in dated}
        assert ids(c.get(reverse(LIST), {"search": "NOPE"})) == set()

    def test_bad_dates_are_400(self, admin):
        c = client_for(admin)
        assert c.get(reverse(LIST), {"created_from": "yesterday"}).status_code == 400
        assert c.get(reverse(LIST), {"created_to": "2026-13-45"}).status_code == 400

    def test_filters_combine_with_status_and_stay_newest_first(self, dated, admin):
        lifecycle.transition(dated[2], "available", admin)
        c = client_for(admin)
        r = c.get(reverse(LIST), {"status": "created", "created_from": day(20)})
        assert [o["id"] for o in r.json()["data"]["results"]] == [
            dated[1].pk,
            dated[0].pk,
        ]
        assert ids(r) == {dated[0].pk, dated[1].pk}

    def test_filters_never_widen_visibility(self, dated, client_user, client2):
        mine = client_for(client_user)
        assert ids(mine.get(reverse(LIST), {"search": "ORD-"})) == {
            dated[0].pk,
            dated[2].pk,
        }
        assert ids(mine.get(reverse(LIST), {"search": dated[1].reference})) == set()
        assert ids(mine.get(reverse(LIST), {"created_from": day(30)})) == {
            dated[0].pk,
            dated[2].pk,
        }

    def test_the_table_carries_the_columns_the_screen_needs(
        self, order, admin, client_user
    ):
        row = client_for(admin).get(reverse(LIST)).json()["data"]["results"][0]
        for key in (
            "reference",
            "client",
            "shop",
            "driver",
            "pickup",
            "delivery",
            "status",
            "delivery_fee",
            "created_at",
        ):
            assert key in row
        assert row["client"]["phone"] == client_user.phone
        assert "history" not in row


class TestTimeline:
    def test_detail_has_history_oldest_first_with_actor_and_reason(
        self, order, admin, client_user
    ):
        lifecycle.transition(order, "available", admin)
        lifecycle.transition(order, "cancelled", client_user, reason="changed my mind")
        h = (
            client_for(admin)
            .get(reverse("order-detail", args=[order.pk]))
            .json()["data"]["order"]["history"]
        )
        assert [(x["from_status"], x["to_status"]) for x in h] == [
            ("", "created"),
            ("created", "available"),
            ("available", "cancelled"),
        ]
        assert h[1]["actor_name"] == admin.full_name
        assert h[2]["reason"] == "changed my mind"
        assert all(x["created_at"] for x in h)

    def test_everyone_who_can_see_the_order_sees_the_timeline(
        self, order, admin, client_user, trader, driver
    ):
        lifecycle.transition(order, "available", admin)
        lifecycle.transition(order, "assigned", admin, driver=driver)
        for user in (client_user, trader, driver, admin):
            r = client_for(user).get(reverse("order-detail", args=[order.pk]))
            assert r.status_code == 200, user.role
            assert len(r.json()["data"]["order"]["history"]) == 3

    def test_nobody_else_gets_the_timeline(self, order, client2, trader2, driver2):
        for user in (client2, trader2, driver2):
            assert (
                client_for(user)
                .get(reverse("order-detail", args=[order.pk]))
                .status_code
                == 404
            )

    def test_the_list_does_not_carry_history(self, order, client_user):
        rows = client_for(client_user).get(reverse(LIST)).json()["data"]["results"]
        assert "history" not in rows[0]
