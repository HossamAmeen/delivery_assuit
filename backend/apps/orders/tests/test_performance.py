import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.orders import performance
from apps.orders.models import Order, OrderRating, OrderStatusChange

from .conftest import client_for, make_order, make_user

pytestmark = pytest.mark.django_db
UTC = datetime.UTC


def at(y, m, d, h=12):
    return datetime.datetime(y, m, d, h, 0, tzinfo=UTC)


def delivered(client, driver, when, score=None, comment=""):
    o = make_order(client, status="delivered", driver=driver)
    OrderStatusChange.objects.create(
        order=o, from_status="in_delivery", to_status="delivered", actor=driver
    )
    OrderStatusChange.objects.filter(order=o, to_status="delivered").update(
        created_at=when
    )
    if score:
        OrderRating.objects.create(
            order=o, client=client, driver=driver, score=score, comment=comment
        )
    return o


def cancelled(client, driver, when):
    o = make_order(client, status="cancelled", driver=driver)
    Order.objects.filter(pk=o.pk).update(cancelled_at=when)
    return o


@pytest.fixture
def sample(client_user, driver, driver2):
    delivered(
        client_user, driver, at(2026, 9, 30, 23), score=5
    )  # last second-ish of September
    delivered(
        client_user, driver, at(2026, 10, 1, 0), score=4
    )  # first minute of October
    delivered(client_user, driver, at(2026, 10, 15), score=3)
    delivered(client_user, driver, at(2026, 10, 31, 23))  # no rating
    cancelled(client_user, driver, at(2026, 10, 5))
    cancelled(client_user, driver, at(2026, 11, 1, 0))
    delivered(client_user, driver2, at(2026, 10, 10), score=1)
    return driver


class TestNumbers:
    def test_all_time(self, sample):
        m = performance.driver_performance(sample.pk)
        assert (m["delivered"], m["cancelled"], m["rating_count"]) == (4, 2, 3)
        assert m["average_rating"] == 4.0
        assert m["month"] is None

    def test_month_boundaries_are_exact(self, sample):
        sep = performance.driver_performance(sample.pk, "2026-09")
        octo = performance.driver_performance(sample.pk, "2026-10")
        nov = performance.driver_performance(sample.pk, "2026-11")
        assert (
            sep["delivered"],
            sep["cancelled"],
            sep["average_rating"],
            sep["rating_count"],
        ) == (1, 0, 5.0, 1)
        assert (
            octo["delivered"],
            octo["cancelled"],
            octo["average_rating"],
            octo["rating_count"],
        ) == (3, 1, 3.5, 2)
        assert (nov["delivered"], nov["cancelled"], nov["average_rating"]) == (
            0,
            1,
            None,
        )

    def test_months_list_is_newest_first_and_adds_up(self, sample):
        months = performance.driver_performance(sample.pk)["months"]
        assert [m["month"] for m in months] == ["2026-11", "2026-10", "2026-09"]
        assert sum(m["delivered"] for m in months) == 4

    def test_other_drivers_are_not_mixed_in(self, sample, driver2):
        m = performance.driver_performance(driver2.pk)
        assert (m["delivered"], m["average_rating"]) == (1, 1.0)

    def test_a_new_driver_has_zeros_and_no_rating(self, driver):
        m = performance.driver_performance(driver.pk)
        assert m == {
            "month": None,
            "delivered": 0,
            "cancelled": 0,
            "average_rating": None,
            "rating_count": 0,
            "months": [],
        }

    def test_orders_cancelled_before_assignment_never_count(self, client_user, driver):
        o = make_order(client_user, status="cancelled")
        Order.objects.filter(pk=o.pk).update(cancelled_at=at(2026, 10, 5))
        assert performance.driver_performance(driver.pk)["cancelled"] == 0

    def test_average_is_rounded_to_one_decimal(self, client_user, driver):
        for s in (5, 4, 4):
            delivered(client_user, driver, at(2026, 10, 2), score=s)
        assert (
            performance.driver_performance(driver.pk, "2026-10")["average_rating"]
            == 4.3
        )

    def test_month_follows_the_server_time_zone(self, client_user, driver):
        # 22:00 UTC on 30 September is already 1 October in Cairo (UTC+3 in summer time).
        delivered(client_user, driver, at(2026, 9, 30, 22))
        assert (
            performance.driver_performance(driver.pk)["months"][0]["month"] == "2026-09"
        )
        timezone.activate("Africa/Cairo")
        try:
            assert (
                performance.driver_performance(driver.pk)["months"][0]["month"]
                == "2026-10"
            )
        finally:
            timezone.deactivate()

    def test_bad_month_is_rejected(self):
        for bad in ("2026-13", "26-10", "october", "2026-1"):
            with pytest.raises(Exception):  # noqa: B017
                performance.parse_month(bad)
        assert (
            performance.parse_month("2026-10") == "2026-10"
            and performance.parse_month("") is None
        )


class TestDriverEndpoint:
    def url(self):
        return reverse("my-performance")

    def test_only_drivers(self, client_user, admin, trader):
        for user in (client_user, admin, trader):
            assert client_for(user).get(self.url()).status_code == 403

    def test_driver_sees_own_aggregates_only(self, sample, driver2):
        data = client_for(sample).get(self.url(), {"month": "2026-10"}).json()["data"]
        assert (data["delivered"], data["cancelled"], data["average_rating"]) == (
            3,
            1,
            3.5,
        )
        assert data["month"] == "2026-10"
        text = str(data)
        assert "comment" not in text and "score" not in text
        other = client_for(driver2).get(self.url()).json()["data"]
        assert other["delivered"] == 1

    def test_new_driver_gets_an_empty_but_valid_answer(self, driver):
        data = client_for(driver).get(self.url()).json()["data"]
        assert (
            data["delivered"] == 0
            and data["average_rating"] is None
            and data["months"] == []
        )

    def test_bad_month_is_400(self, driver):
        assert (
            client_for(driver).get(self.url(), {"month": "2026-99"}).status_code == 400
        )


class TestStaffOverview:
    url = "staff-driver-performance"

    def rows(self, c, **params):
        return c.get(reverse(self.url), params).json()["data"]["results"]

    def test_staff_only(self, client_user, driver, trader):
        for user in (client_user, driver, trader):
            assert client_for(user).get(reverse(self.url)).status_code == 403

    def test_rows_match_the_orders_and_default_sort_is_delivered(
        self, sample, driver2, admin
    ):
        rows = self.rows(client_for(admin))
        assert [r["id"] for r in rows] == [sample.pk, driver2.pk]
        assert rows[0]["delivered"] == 4 and rows[0]["cancelled"] == 2
        assert rows[0]["average_rating"] == 4.0 and rows[0]["rating_count"] == 3
        assert set(rows[0]) == {
            "id",
            "full_name",
            "status",
            "delivered",
            "cancelled",
            "average_rating",
            "rating_count",
        }

    def test_month_filter(self, sample, driver2, manager):
        rows = {r["id"]: r for r in self.rows(client_for(manager), month="2026-09")}
        assert rows[sample.pk]["delivered"] == 1 and rows[driver2.pk]["delivered"] == 0

    def test_sort_by_rating_puts_unrated_last(
        self, client_user, driver, driver2, admin
    ):
        driver3 = make_user("driver3", "driver", "01000000032")
        delivered(client_user, driver, at(2026, 10, 2), score=3)
        delivered(client_user, driver2, at(2026, 10, 2), score=5)
        delivered(client_user, driver3, at(2026, 10, 2))
        rows = self.rows(client_for(admin), ordering="rating")
        assert [r["id"] for r in rows] == [driver2.pk, driver.pk, driver3.pk]

    def test_bad_ordering_and_month_are_400(self, admin):
        c = client_for(admin)
        assert c.get(reverse(self.url), {"ordering": "name"}).status_code == 400
        assert c.get(reverse(self.url), {"month": "nope"}).status_code == 400

    def test_includes_pending_drivers_with_zeros_and_is_paginated(self, admin, driver):
        make_user("d_p", "driver", "01099990101", status="pending_approval")
        data = client_for(admin).get(reverse(self.url), {"page_size": 1}).json()["data"]
        assert data["count"] == 2 and len(data["results"]) == 1 and data["next"]

    def test_deleted_drivers_are_hidden(self, admin, driver):
        driver.soft_delete()
        assert self.rows(client_for(admin)) == []
