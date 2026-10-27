import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.orders import assign
from apps.orders.models import Order, OrderStatusChange

from .conftest import client_for, make_order, make_user

pytestmark = pytest.mark.django_db


def do_assign(c, order_pk, driver_pk):
    return c.post(
        reverse("order-assign", args=[order_pk]), {"driver": driver_pk}, format="json"
    )


@pytest.fixture
def available(client_user, shop, admin):
    o = make_order(client_user, shop=shop, status="available")
    OrderStatusChange.objects.create(
        order=o, from_status="created", to_status="available", actor=admin
    )
    return o


class TestAccess:
    def test_anonymous_is_401(self, available, driver):
        assert (
            APIClient().post(reverse("order-assign", args=[available.pk])).status_code
            == 401
        )

    @pytest.mark.parametrize("role", ["client", "trader", "driver"])
    def test_other_roles_are_403(self, role, available, driver):
        c = client_for(make_user(f"u_{role}", role, "01099990001"))
        assert do_assign(c, available.pk, driver.pk).status_code == 403
        assert Order.objects.get(pk=available.pk).status == "available"

    def test_unknown_order_is_404(self, admin, driver):
        assert do_assign(client_for(admin), 9999, driver.pk).status_code == 404

    def test_missing_driver_is_400(self, admin, available):
        r = client_for(admin).post(
            reverse("order-assign", args=[available.pk]), {}, format="json"
        )
        assert "driver" in r.json()["errors"]


@pytest.mark.parametrize("who", ["admin", "manager"])
class TestAssign:
    def test_assigns_and_records_who_and_when(self, who, available, driver, request):
        staff = request.getfixturevalue(who)
        r = do_assign(client_for(staff), available.pk, driver.pk)
        assert r.status_code == 200
        data = r.json()["data"]["order"]
        assert data["status"] == "assigned"
        assert data["driver"] == {"id": driver.pk, "full_name": driver.full_name}
        row = OrderStatusChange.objects.filter(order=available).last()
        assert (row.to_status, row.actor_id) == ("assigned", staff.pk)
        assert Order.objects.get(pk=available.pk).driver_id == driver.pk


class TestRules:
    @pytest.mark.parametrize(
        "status",
        ["created", "assigned", "picked_up", "in_delivery", "delivered", "cancelled"],
    )
    def test_only_available_orders(self, status, admin, client_user, driver, driver2):
        o = make_order(
            client_user,
            status=status,
            driver=driver2 if status not in ("created", "cancelled") else None,
        )
        r = do_assign(client_for(admin), o.pk, driver.pk)
        assert r.status_code == 400
        assert "status" in r.json()["errors"]
        assert Order.objects.get(pk=o.pk).status == status

    @pytest.mark.parametrize(
        "kind",
        [
            "client",
            "trader",
            "manager",
            "pending",
            "deactivated",
            "rejected",
            "unknown",
        ],
    )
    def test_only_active_drivers(
        self, kind, admin, available, client_user, trader, manager
    ):
        others = {
            "client": client_user,
            "trader": trader,
            "manager": manager,
            "pending": make_user(
                "d_p", "driver", "01099990101", status="pending_approval"
            ),
            "deactivated": make_user(
                "d_d", "driver", "01099990102", status="deactivated"
            ),
            "rejected": make_user("d_r", "driver", "01099990103", status="rejected"),
        }
        pk = 99999 if kind == "unknown" else others[kind].pk
        r = do_assign(client_for(admin), available.pk, pk)
        assert r.status_code == 400
        assert "driver" in r.json()["errors"]
        assert Order.objects.get(pk=available.pk).driver_id is None

    def test_a_busy_driver_is_refused_br1(self, admin, available, client_user, driver):
        for status in ("assigned", "picked_up", "in_delivery"):
            busy = make_order(client_user, status=status, driver=driver)
            r = do_assign(client_for(admin), available.pk, driver.pk)
            assert r.status_code == 400, status
            assert "already has an active order" in r.json()["errors"]["driver"][0]
            busy.status = "delivered"
            busy.save()
        # once the earlier order is delivered the driver is free again
        assert do_assign(client_for(admin), available.pk, driver.pk).status_code == 200

    def test_a_cancelled_active_order_frees_the_driver(
        self, admin, available, client_user, driver
    ):
        busy = make_order(client_user, status="assigned", driver=driver)
        assert do_assign(client_for(admin), available.pk, driver.pk).status_code == 400
        busy.status = "cancelled"
        busy.save()
        assert do_assign(client_for(admin), available.pk, driver.pk).status_code == 200

    def test_second_assignment_of_the_same_order_loses(
        self, admin, manager, available, driver, driver2
    ):
        first = do_assign(client_for(admin), available.pk, driver.pk)
        second = do_assign(client_for(manager), available.pk, driver2.pk)
        assert first.status_code == 200
        assert second.status_code == 400
        assert Order.objects.get(pk=available.pk).driver_id == driver.pk
        assert (
            OrderStatusChange.objects.filter(
                order=available, to_status="assigned"
            ).count()
            == 1
        )

    def test_one_driver_cannot_take_two_orders(self, admin, client_user, shop, driver):
        a = make_order(client_user, shop=shop, status="available")
        b = make_order(client_user, shop=shop, status="available")
        c = client_for(admin)
        assert do_assign(c, a.pk, driver.pk).status_code == 200
        assert do_assign(c, b.pk, driver.pk).status_code == 400
        assert Order.objects.get(pk=b.pk).status == "available"

    def test_service_level_check(self, admin, available, driver):
        assign.assign(available, admin, driver.pk)
        assert assign.has_active_order(driver)


class TestDriverList:
    def test_staff_see_active_drivers_with_busy_state(
        self, admin, client_user, driver, driver2
    ):
        o = make_order(client_user, status="assigned", driver=driver)
        make_user("d_p", "driver", "01099990101", status="pending_approval")
        make_user("d_x", "driver", "01099990102", status="deactivated")
        rows = client_for(admin).get(reverse("driver-list")).json()["data"]["results"]
        assert {r["id"] for r in rows} == {driver.pk, driver2.pk}
        by_id = {r["id"]: r for r in rows}
        assert by_id[driver.pk]["has_active_order"] is True
        assert by_id[driver.pk]["active_order_reference"] == o.reference
        assert by_id[driver2.pk]["has_active_order"] is False
        assert by_id[driver2.pk]["active_order_reference"] is None
        assert set(by_id[driver.pk]) == {
            "id",
            "full_name",
            "phone",
            "has_active_order",
            "active_order_reference",
        }

    def test_available_filter(self, manager, client_user, driver, driver2):
        make_order(client_user, status="in_delivery", driver=driver)
        c = client_for(manager)
        free = c.get(reverse("driver-list"), {"available": "true"}).json()["data"][
            "results"
        ]
        assert [r["id"] for r in free] == [driver2.pk]
        busy = c.get(reverse("driver-list"), {"available": "false"}).json()["data"][
            "results"
        ]
        assert [r["id"] for r in busy] == [driver.pk]

    @pytest.mark.parametrize("role", ["client", "trader", "driver"])
    def test_other_roles_are_403(self, role):
        c = client_for(make_user(f"u_{role}", role, "01099990001"))
        assert c.get(reverse("driver-list")).status_code == 403

    def test_anonymous_is_401(self):
        assert APIClient().get(reverse("driver-list")).status_code == 401

    def test_deleted_driver_is_not_listed(self, admin, driver):
        driver.soft_delete()
        assert (
            client_for(admin).get(reverse("driver-list")).json()["data"]["count"] == 0
        )
