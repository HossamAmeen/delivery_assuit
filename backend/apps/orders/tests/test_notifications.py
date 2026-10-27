import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.locations.models import Location
from apps.notifications import services
from apps.notifications.models import Notification
from apps.orders import lifecycle
from apps.shops.models import ShopItem

from .conftest import client_for, make_order, make_user

pytestmark = pytest.mark.django_db


def kinds(user):
    return list(
        Notification.objects.filter(user=user)
        .order_by("id")
        .values_list("kind", flat=True)
    )


@pytest.fixture
def open_shop(shop, trader):
    shop.is_available = True
    shop.save()
    Location.objects.create(owner=trader, name="Main", address="12 Nile St")
    return shop


def place_order(client_user, open_shop):
    item = ShopItem.objects.create(shop=open_shop, name="Pie")
    return (
        client_for(client_user)
        .post(
            reverse("order-list"),
            {
                "shop": open_shop.pk,
                "items": [{"item": item.pk, "quantity": 1}],
                "delivery": {"name": "Home", "address": "5 Garden St"},
            },
            format="json",
        )
        .json()["data"]["order"]
    )


class TestRecipients:
    def test_new_order_notifies_every_admin_and_manager_only(
        self, open_shop, client_user, admin, manager, trader, driver
    ):
        place_order(client_user, open_shop)
        assert kinds(admin) == ["order_waiting_review"]
        assert kinds(manager) == ["order_waiting_review"]
        for other in (client_user, trader, driver):
            assert kinds(other) == []

    def test_inactive_staff_are_not_notified(
        self, open_shop, client_user, admin, manager
    ):
        manager.status = "deactivated"
        manager.save()
        place_order(client_user, open_shop)
        assert kinds(manager) == [] and kinds(admin) == ["order_waiting_review"]

    def test_the_full_journey_tells_the_right_people(
        self, open_shop, client_user, admin, driver
    ):
        order = place_order(client_user, open_shop)
        c_admin, c_driver = client_for(admin), client_for(driver)
        c_admin.post(reverse("order-approve", args=[order["id"]]), {}, format="json")
        c_admin.post(
            reverse("order-assign", args=[order["id"]]),
            {"driver": driver.pk},
            format="json",
        )
        for _ in range(3):
            c_driver.post(reverse("order-advance", args=[order["id"]]))
        assert kinds(client_user) == [
            "order_approved",
            "order_assigned",
            "order_picked_up",
            "order_in_delivery",
            "order_delivered",
        ]
        assert kinds(driver) == ["order_assigned"]
        assert kinds(admin) == ["order_waiting_review"]

    def test_review_rejection_goes_to_the_client(self, open_shop, client_user, admin):
        order = place_order(client_user, open_shop)
        client_for(admin).post(
            reverse("order-reject", args=[order["id"]]),
            {"reason": "Unclear"},
            format="json",
        )
        assert kinds(client_user) == ["order_rejected"]

    def test_staff_cancel_after_assignment_tells_client_and_driver(
        self, client_user, driver, admin
    ):
        o = make_order(client_user, status="assigned", driver=driver)
        client_for(admin).post(
            reverse("order-cancel", args=[o.pk]), {"reason": "Stopped"}, format="json"
        )
        assert kinds(client_user) == ["order_cancelled"]
        assert kinds(driver) == ["order_cancelled"]

    def test_staff_cancel_before_assignment_tells_only_the_client(
        self, client_user, driver, admin
    ):
        o = make_order(client_user, status="available")
        client_for(admin).post(
            reverse("order-cancel", args=[o.pk]), {"reason": "Stopped"}, format="json"
        )
        assert kinds(client_user) == ["order_cancelled"] and kinds(driver) == []

    def test_a_client_cancelling_their_own_order_is_not_told_about_it(
        self, client_user, admin
    ):
        o = make_order(client_user, status="available")
        client_for(client_user).post(
            reverse("order-cancel", args=[o.pk]), {}, format="json"
        )
        assert kinds(client_user) == []

    def test_editing_an_approved_order_sends_it_back_to_staff(
        self, client_user, admin, manager
    ):
        o = make_order(client_user, status="available")
        client_for(client_user).patch(
            reverse("order-detail", args=[o.pk]),
            {"description": "Changed box"},
            format="json",
        )
        assert kinds(admin) == kinds(manager) == ["order_waiting_review"]

    def test_new_driver_and_trader_registrations_notify_staff_clients_do_not(
        self, admin, manager
    ):
        c = APIClient()
        for role, phone in (
            ("driver", "01011110001"),
            ("trader", "01011110002"),
            ("client", "01011110003"),
        ):
            r = c.post(
                reverse(f"register-{role}"),
                {
                    "full_name": f"New {role}",
                    "phone": phone,
                    "password": "Zx9!kLm2#QwErTy",
                },
                format="json",
            )
            assert r.status_code == 201, r.content
        assert kinds(admin) == ["account_waiting_approval"] * 2
        assert kinds(manager) == ["account_waiting_approval"] * 2

    def test_payload_carries_the_order(self, open_shop, client_user, admin):
        order = place_order(client_user, open_shop)
        row = (
            client_for(admin)
            .get(reverse("notification-list"))
            .json()["data"]["results"][0]
        )
        assert row["order_id"] == order["id"] and row["reference"] == order["reference"]
        assert row["kind"] == "order_waiting_review" and row["read"] is False


class TestEndpoints:
    def test_anonymous_is_401(self):
        assert APIClient().get(reverse("notification-list")).status_code == 401

    def test_users_see_only_their_own_newest_first_and_can_filter_unread(
        self, client_user, client2
    ):
        o = make_order(client_user)
        services._send([client_user], "order_approved", o)
        services._send([client_user], "order_assigned", o)
        services._send([client2], "order_approved", o)
        c = client_for(client_user)
        rows = c.get(reverse("notification-list")).json()["data"]["results"]
        assert [r["kind"] for r in rows] == ["order_assigned", "order_approved"]
        c.post(reverse("notification-read", args=[rows[0]["id"]]))
        unread = c.get(reverse("notification-list"), {"unread": "true"}).json()["data"][
            "results"
        ]
        assert [r["kind"] for r in unread] == ["order_approved"]

    def test_unread_count(self, client_user):
        o = make_order(client_user)
        for _ in range(3):
            services._send([client_user], "order_approved", o)
        assert (
            client_for(client_user)
            .get(reverse("notification-unread"))
            .json()["data"]["count"]
            == 3
        )

    def test_mark_read_is_idempotent_and_only_for_the_owner(self, client_user, client2):
        o = make_order(client_user)
        services._send([client_user], "order_approved", o)
        nid = Notification.objects.get().pk
        assert (
            client_for(client2)
            .post(reverse("notification-read", args=[nid]))
            .status_code
            == 404
        )
        assert Notification.objects.get().read_at is None
        c = client_for(client_user)
        first = c.post(reverse("notification-read", args=[nid])).json()["data"][
            "notification"
        ]
        again = c.post(reverse("notification-read", args=[nid]))
        assert first["read"] is True and again.status_code == 200

    def test_read_all_marks_only_my_own(self, client_user, client2):
        o = make_order(client_user)
        services._send([client_user, client2], "order_approved", o)
        services._send([client_user], "order_assigned", o)
        r = client_for(client_user).post(reverse("notification-read-all"))
        assert r.json()["data"]["marked"] == 2
        assert (
            Notification.objects.filter(user=client2, read_at__isnull=True).count() == 1
        )

    def test_a_deactivated_account_is_refused(self, client_user):
        c = client_for(client_user)
        client_user.status = "deactivated"
        client_user.save()
        assert c.get(reverse("notification-list")).status_code == 403

    def test_list_is_paginated(self, client_user):
        o = make_order(client_user)
        for _ in range(3):
            services._send([client_user], "order_approved", o)
        data = (
            client_for(client_user)
            .get(reverse("notification-list"), {"page_size": 2})
            .json()["data"]
        )
        assert data["count"] == 3 and len(data["results"]) == 2 and data["next"]


def test_a_notification_failure_never_blocks_the_action(
    monkeypatch, client_user, admin
):
    def boom(*a, **k):
        raise RuntimeError("down")

    monkeypatch.setattr(services.Notification.objects, "bulk_create", boom)
    o = make_order(client_user, status="created")
    lifecycle.transition(o, "available", admin)
    o.refresh_from_db()
    assert o.status == "available"


def test_make_user_import():
    assert make_user
