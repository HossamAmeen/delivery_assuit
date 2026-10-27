import pytest


@pytest.fixture(autouse=True)
def _test_env(settings):
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }
