import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.audit import services
from apps.audit.models import AuditEntry
from apps.shops.models import ShopItem

from .conftest import client_for, make_order, make_user

pytestmark = pytest.mark.django_db
URL = "staff-audit"


def entries(**filters):
    return list(AuditEntry.objects.filter(**filters).order_by("id"))


class TestRecording:
    def test_status_changes_are_logged_with_actor_and_detail(
        self, client_user, admin, driver
    ):
        o = make_order(client_user, status="created")
        c = client_for(admin)
        c.post(
            reverse("order-approve", args=[o.pk]), {"delivery_fee": 20}, format="json"
        )
        c.post(
            reverse("order-assign", args=[o.pk]), {"driver": driver.pk}, format="json"
        )
        client_for(driver).post(reverse("order-advance", args=[o.pk]))
        rows = entries(target_type="order", target_id=o.pk, action="order.status")
        assert [(r.detail, r.actor_id) for r in rows] == [
            ("-> created", client_user.pk),
            ("created -> available", admin.pk),
            ("available -> assigned", admin.pk),
            ("assigned -> picked_up", driver.pk),
        ]
        assert all(r.created_at for r in rows)

    def test_creation_is_logged(self, client_user, shop, trader):
        from apps.locations.models import Location

        shop.is_available = True
        shop.save()
        Location.objects.create(owner=trader, name="Main", address="12 Nile St")
        item = ShopItem.objects.create(shop=shop, name="Pie")
        r = client_for(client_user).post(
            reverse("order-list"),
            {
                "shop": shop.pk,
                "items": [{"item": item.pk, "quantity": 1}],
                "delivery": {"name": "Home", "address": "5 Garden St"},
            },
            format="json",
        )
        pk = r.json()["data"]["order"]["id"]
        assert [x.detail for x in entries(target_type="order", target_id=pk)] == [
            "-> created"
        ]

    def test_fee_changes_cancellations_ratings_and_prices(
        self, client_user, admin, driver, shop
    ):
        o = make_order(client_user, status="available")
        c = client_for(admin)
        c.patch(reverse("order-fee", args=[o.pk]), {"delivery_fee": 10}, format="json")
        c.patch(
            reverse("order-fee", args=[o.pk]), {"delivery_fee": 12.5}, format="json"
        )
        assert [r.detail for r in entries(action="order.fee")] == [
            "None -> 10.00",
            "10.00 -> 12.50",
        ]
        c.post(
            reverse("order-cancel", args=[o.pk]), {"reason": "Stopped"}, format="json"
        )
        assert entries(action="order.status")[-1].detail == "available -> cancelled"
        d = make_order(client_user, status="delivered", driver=driver)
        client_for(client_user).post(
            reverse("order-rating", args=[d.pk]), {"score": 4}, format="json"
        )
        assert entries(action="order.rating")[0].detail == "score 4"
        item = ShopItem.objects.create(shop=shop, name="Pie")
        c.patch(
            reverse("staff-item-price", args=[item.pk]), {"price": 9}, format="json"
        )
        assert entries(action="item.price")[0].target_id == item.pk

    def test_account_actions(self, admin, manager):
        t = make_user("t_p", "trader", "01099990201", status="pending_approval")
        c = client_for(admin)
        c.post(reverse("user-approve", args=[t.pk]))
        c.post(reverse("user-deactivate", args=[t.pk]))
        c.post(reverse("user-activate", args=[t.pk]))
        assert [r.action for r in entries(target_type="user", target_id=t.pk)] == [
            "account.approved",
            "account.deactivated",
            "account.activated",
        ]
        p = make_user("d_p", "driver", "01099990101", status="pending_approval")
        client_for(manager).post(
            reverse("user-reject", args=[p.pk]), {"reason": "No licence"}, format="json"
        )
        row = entries(target_id=p.pk, action="account.rejected")[0]
        assert row.detail == "No licence" and row.actor_id == manager.pk

    def test_refused_actions_leave_nothing_behind(self, client_user, driver):
        o = make_order(client_user, status="created")
        client_for(driver).post(reverse("order-advance", args=[o.pk]))
        assert entries(
            target_type="order", target_id=o.pk, action="order.status"
        ) == [] or all(
            e.detail == "-> created"
            for e in entries(target_type="order", target_id=o.pk)
        )


class TestReading:
    def test_anonymous_is_401(self):
        assert APIClient().get(reverse(URL)).status_code == 401

    @pytest.mark.parametrize("role", ["client", "trader", "driver"])
    def test_only_staff_can_read(self, role):
        assert (
            client_for(make_user(f"u_{role}", role, "01099990009"))
            .get(reverse(URL))
            .status_code
            == 403
        )

    def test_staff_read_newest_first_with_filters(
        self, client_user, admin, manager, driver
    ):
        o = make_order(client_user, status="created")
        client_for(admin).post(reverse("order-approve", args=[o.pk]), {}, format="json")
        client_for(manager).post(
            reverse("order-assign", args=[o.pk]), {"driver": driver.pk}, format="json"
        )
        c = client_for(admin)
        rows = c.get(reverse(URL)).json()["data"]["results"]
        assert rows[0]["detail"] == "available -> assigned"
        assert rows[0]["actor"] == {"id": manager.pk, "full_name": manager.full_name}
        by_actor = c.get(reverse(URL), {"actor": admin.pk}).json()["data"]["results"]
        assert {r["actor"]["id"] for r in by_actor} == {admin.pk}
        by_action = c.get(
            reverse(URL),
            {"action": "order.status", "target_type": "order", "target_id": o.pk},
        )
        assert by_action.json()["data"]["count"] == 3
        assert c.get(reverse(URL), {"action": "nope"}).json()["data"]["count"] == 0

    def test_no_write_endpoints_exist(self, admin):
        c = client_for(admin)
        for method in (c.post, c.put, c.patch, c.delete):
            assert method(reverse(URL)).status_code == 405

    def test_paginated(self, admin):
        for i in range(3):
            services.log(admin, "x.y", "order", i)
        data = client_for(admin).get(reverse(URL), {"page_size": 2}).json()["data"]
        assert data["count"] == 3 and len(data["results"]) == 2 and data["next"]


class TestAppendOnly:
    def test_entries_cannot_be_changed_or_removed_in_code(self, admin):
        services.log(admin, "x.y", "order", 1, "first")
        entry = AuditEntry.objects.get()
        entry.detail = "tampered"
        with pytest.raises(PermissionError):
            entry.save()
        with pytest.raises(PermissionError):
            entry.delete()
        with pytest.raises(PermissionError):
            AuditEntry.objects.filter(pk=entry.pk).update(detail="tampered")
        with pytest.raises(PermissionError):
            AuditEntry.objects.all().delete()
        assert AuditEntry.objects.get().detail == "first"

    def test_a_logging_failure_never_blocks_the_action(self, monkeypatch, admin):
        monkeypatch.setattr(
            AuditEntry.objects,
            "create",
            lambda **k: (_ for _ in ()).throw(RuntimeError("down")),
        )
        services.log(admin, "x.y", "order", 1)  # must not raise
        assert AuditEntry.objects.count() == 0

    def test_long_detail_is_cut(self, admin):
        services.log(admin, "x.y", "order", 1, "a" * 400)
        assert len(AuditEntry.objects.get().detail) == 255

    def test_the_audit_model_is_not_in_the_django_admin(self):
        from django.contrib import admin as dj_admin

        assert AuditEntry not in dj_admin.site._registry
