import pytest

from apps.users.tests.conftest import client_for, make_user


@pytest.fixture(autouse=True)
def isolated_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "locations-tests",
        }
    }
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def trader(db):
    return make_user("trader1", "trader", "01000000010")


@pytest.fixture
def trader2(db):
    return make_user("trader2", "trader", "01000000011")


@pytest.fixture
def client_user(db):
    return make_user("client1", "client", "01000000020")


@pytest.fixture
def trader_client(trader):
    return client_for(trader)


@pytest.fixture
def trader2_client(trader2):
    return client_for(trader2)
