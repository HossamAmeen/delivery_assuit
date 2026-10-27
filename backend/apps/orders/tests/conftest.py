# ruff: noqa: F401, F811
import pytest

from apps.locations.tests.conftest import (
    client_for,
    client_user,
    isolated_cache,
    make_user,
    trader,
    trader2,
    trader2_client,
    trader_client,
)
from apps.orders import lifecycle
from apps.orders.models import Order, OrderItem
from apps.shops.services import get_or_create_shop


@pytest.fixture
def admin(db):
    return make_user("admin1", "admin", "01000000001")


@pytest.fixture
def manager(db):
    return make_user("manager1", "manager", "01000000002")


@pytest.fixture
def driver(db):
    return make_user("driver1", "driver", "01000000030")


@pytest.fixture
def driver2(db):
    return make_user("driver2", "driver", "01000000031")


@pytest.fixture
def client2(db):
    return make_user("client2", "client", "01000000021")


def make_order(client, shop=None, status="created", driver=None, **extra):
    """An order straight in the database, in any status (tests only)."""
    order = Order.objects.create(
        client=client,
        shop=shop,
        driver=driver,
        status=status,
        pickup_name="Main branch",
        pickup_address="12 Nile St",
        delivery_name="Home",
        delivery_address="5 Garden St",
        description=extra.pop("description", "A box"),
        **extra,
    )
    lifecycle.record_creation(order, client)
    return order


@pytest.fixture
def shop(trader):
    return get_or_create_shop(trader)


@pytest.fixture
def order(client_user, shop):
    o = make_order(client_user, shop=shop)
    OrderItem.objects.create(order=o, name="Cheese pie", quantity=2)
    return o
