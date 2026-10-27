import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from rest_framework.test import APIClient

from config.settings.secrets import validate_secrets

BACKEND = Path(__file__).resolve().parents[2]
GOOD_KEY = "k" * 40


# --- VULN-004: JSON only ----------------------------------------------------------


def get(settings, path="/api/v1/health/", **headers):
    settings.HEALTH_CHECK_PASSWORD = "pw"
    return APIClient().get(path, HTTP_X_HEALTH_CHECK_TOKEN="pw", **headers)


@pytest.mark.parametrize(
    "accept", ["text/html,application/xhtml+xml,*/*;q=0.8", "*/*", "application/json"]
)
def test_api_returns_json_for_browser_like_accept_headers(settings, accept):
    r = get(settings, HTTP_ACCEPT=accept)
    assert r.status_code == 200
    assert r["Content-Type"].startswith("application/json")


def test_html_only_accept_is_refused_with_a_json_406(settings):
    r = get(settings, HTTP_ACCEPT="text/html")
    assert r.status_code == 406
    assert r["Content-Type"].startswith("application/json")


def test_browsable_api_format_is_not_available(settings):
    r = get(settings, path="/api/v1/health/?format=api")
    assert r.status_code == 404
    assert r["Content-Type"].startswith("application/json")


@pytest.mark.django_db
def test_docs_still_work():
    c = APIClient()
    assert c.get("/api/docs/").status_code == 200
    assert c.get("/api/schema/?format=json").status_code == 200


# --- VULN-005: placeholder secrets ------------------------------------------------


@pytest.mark.parametrize(
    "key",
    [
        "",
        "short",
        "change-me",
        "x" * 31,
        "change-me-" + "x" * 40,
        "insecure-" + "x" * 40,
    ],
)
def test_weak_or_placeholder_secret_key_rejected(key):
    with pytest.raises(ImproperlyConfigured):
        validate_secrets(key, "")


@pytest.mark.parametrize("pw", ["change-me", "ChangeMe", "change-me-health"])
def test_placeholder_health_password_rejected(pw):
    with pytest.raises(ImproperlyConfigured):
        validate_secrets(GOOD_KEY, pw)


def test_real_secrets_and_empty_health_password_accepted():
    validate_secrets(GOOD_KEY, "")
    validate_secrets(GOOD_KEY, "a-real-health-password-91")


def load(module, **env):
    full = {
        **os.environ,
        "DATABASE_URL": "postgres://u:p@localhost/db",
        "RATELIMIT_CACHE_URL": "redis://localhost:6379/2",
        "CELERY_BROKER_URL": "redis://localhost:6379/0",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/1",
        "ALLOWED_HOSTS": "example.org",
        **env,
    }
    return subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        cwd=BACKEND,
        env=full,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    "module", ["config.settings.production", "config.settings.staging"]
)
def test_production_and_staging_refuse_placeholders(module):
    bad = load(module, SECRET_KEY="change-me", HEALTH_CHECK_PASSWORD="change-me")
    assert bad.returncode != 0
    assert "ImproperlyConfigured" in bad.stderr
    good = load(module, SECRET_KEY=GOOD_KEY, HEALTH_CHECK_PASSWORD="real-health-pw-77")
    assert good.returncode == 0, good.stderr[-400:]


def test_development_settings_unaffected():
    r = subprocess.run(
        [sys.executable, "-c", "import config.settings.development"],
        cwd=BACKEND,
        env={**os.environ, "SECRET_KEY": "change-me"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0
