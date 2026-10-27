from django.conf import settings
from django.core.management import call_command


def test_settings_load_without_celery_or_redis():
    assert settings.CELERY_ENABLED is False
    assert settings.CACHES["default"]["BACKEND"].endswith("LocMemCache")


def test_django_check_passes():
    call_command("check")


def test_openapi_schema_served(client):
    assert client.get("/api/schema/").status_code == 200
