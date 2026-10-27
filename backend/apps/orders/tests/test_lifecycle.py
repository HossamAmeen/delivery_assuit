import itertools

import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.orders import lifecycle
from apps.orders.models import Order, OrderStatusChange

from .conftest import make_order

pytestmark = pytest.mark.django_db
S = Order.Status
ALL = list(S)


@pytest.fixture
def people(admin, manager, client_user, client2, driver, driver2, trader):
    return {
        "admin": admin,
        "manager": manager,
        "owner": client_user,
        "other_client": client2,
        "driver": driver,
        "other_driver": driver2,
        "trader": trader,
    }


# who may make each valid move
WHO = {
    (S.CREATED, S.AVAILABLE): {"admin", "manager"},
    (S.CREATED, S.CANCELLED): {"admin", "manager", "owner"},
    (S.AVAILABLE, S.CREATED): {"admin", "manager", "owner"},
    (S.AVAILABLE, S.ASSIGNED): {"admin", "manager"},
    (S.AVAILABLE, S.CANCELLED): {"admin", "manager", "owner"},
    (S.ASSIGNED, S.PICKED_UP): {"driver"},
    (S.ASSIGNED, S.CANCELLED): {"admin", "manager"},
    (S.PICKED_UP, S.IN_DELIVERY): {"driver"},
    (S.PICKED_UP, S.CANCELLED): {"admin", "manager"},
    (S.IN_DELIVERY, S.DELIVERED): {"driver"},
    (S.IN_DELIVERY, S.CANCELLED): {"admin", "manager"},
}


def order_in(status, people, shop=None):
    assigned = status in (S.ASSIGNED, S.PICKED_UP, S.IN_DELIVERY, S.DELIVERED)
    return make_order(
        people["owner"],
        shop=shop,
        status=status,
        driver=people["driver"] if assigned else None,
    )


def move(order, to, actor, people):
    kwargs = {"driver": people["driver"]} if to == S.ASSIGNED else {}
    return lifecycle.transition(order, to, actor, reason="why", **kwargs)


@pytest.mark.parametrize(("frm", "to"), list(itertools.product(ALL, ALL)))
def test_every_pair_and_every_role(frm, to, people):
    """The full matrix: 49 status pairs times 7 kinds of caller."""
    for name, actor in people.items():
        order = order_in(frm, people)
        if (frm, to) not in WHO:
            with pytest.raises(ValidationError) as err:
                move(order, to, actor, people)
            assert "status" in err.value.detail
            assert order.status == frm
        elif name in WHO[(frm, to)]:
            moved = move(order, to, actor, people)
            assert moved.status == to
            assert Order.objects.get(pk=order.pk).status == to
        else:
            with pytest.raises(PermissionDenied):
                move(order, to, actor, people)
            assert Order.objects.get(pk=order.pk).status == frm


def test_history_records_who_and_when(people):
    order = order_in(S.CREATED, people)
    lifecycle.transition(order, S.AVAILABLE, people["admin"])
    rows = list(OrderStatusChange.objects.filter(order=order))
    assert [(r.from_status, r.to_status, r.actor_id) for r in rows] == [
        ("", "created", people["owner"].pk),
        ("created", "available", people["admin"].pk),
    ]
    assert rows[-1].created_at is not None


def test_refused_moves_write_no_history(people):
    order = order_in(S.CREATED, people)
    with pytest.raises(ValidationError):
        lifecycle.transition(order, S.DELIVERED, people["admin"])
    with pytest.raises(PermissionDenied):
        lifecycle.transition(order, S.AVAILABLE, people["owner"])
    assert OrderStatusChange.objects.filter(order=order).count() == 1


def test_full_happy_path(people):
    order = order_in(S.CREATED, people)
    lifecycle.transition(order, S.AVAILABLE, people["manager"])
    lifecycle.transition(order, S.ASSIGNED, people["admin"], driver=people["driver"])
    assert order.driver_id == people["driver"].pk
    lifecycle.transition(order, S.PICKED_UP, people["driver"])
    lifecycle.transition(order, S.IN_DELIVERY, people["driver"])
    lifecycle.transition(order, S.DELIVERED, people["driver"])
    assert order.status == S.DELIVERED
    assert OrderStatusChange.objects.filter(order=order).count() == 6


def test_final_states_are_final_with_a_clear_message(people):
    for final in (S.DELIVERED, S.CANCELLED):
        order = order_in(final, people)
        with pytest.raises(ValidationError) as err:
            lifecycle.transition(order, S.AVAILABLE, people["admin"])
        assert "final" in str(err.value.detail["status"][0])


def test_cancel_stores_reason_actor_and_time(people):
    order = order_in(S.AVAILABLE, people)
    lifecycle.transition(order, S.CANCELLED, people["owner"], reason="changed my mind")
    order.refresh_from_db()
    assert order.cancel_reason == "changed my mind"
    assert order.cancelled_by_id == people["owner"].pk
    assert order.cancelled_at is not None


@pytest.mark.parametrize("kind", ["none", "client", "pending_driver", "deactivated"])
def test_assign_needs_an_active_driver(kind, people):
    from apps.users.tests.conftest import make_user

    order = order_in(S.AVAILABLE, people)
    chosen = {
        "none": None,
        "client": people["owner"],
        "pending_driver": make_user(
            "pd", "driver", "01099990101", status="pending_approval"
        ),
        "deactivated": make_user("dd", "driver", "01099990102", status="deactivated"),
    }[kind]
    with pytest.raises(ValidationError):
        lifecycle.transition(order, S.ASSIGNED, people["admin"], driver=chosen)
    assert Order.objects.get(pk=order.pk).driver_id is None


def test_a_non_active_staff_account_cannot_move_an_order(people):
    order = order_in(S.CREATED, people)
    people["admin"].status = "deactivated"
    people["admin"].save()
    with pytest.raises(PermissionDenied):
        lifecycle.transition(order, S.AVAILABLE, people["admin"])


def test_reference_is_unique_padded_and_stable(people):
    a = order_in(S.CREATED, people)
    b = order_in(S.CREATED, people)
    assert a.reference == f"ORD-{a.pk:06d}"
    assert a.reference != b.reference
    a.description = "edited"
    a.save()
    assert Order.objects.get(pk=a.pk).reference == f"ORD-{a.pk:06d}"
