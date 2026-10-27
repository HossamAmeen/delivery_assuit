import pytest


@pytest.fixture(autouse=True)
def fast_password_hasher(request, settings):
    """Cheap hashing keeps the suite fast. Timing tests keep the real hasher."""
    from apps.users import services

    services._dummy_hash.cache_clear()
    if not request.module.__name__.endswith("test_timing"):
        settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    yield
    services._dummy_hash.cache_clear()
