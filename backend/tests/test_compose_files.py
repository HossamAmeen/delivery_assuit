"""Static checks for the compose files. Docker itself is not run (PO decision 2026-10-08)."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]

# Inside the dev container only ./backend is mounted, so the repo-root files do not exist there.
if not (ROOT / "docker-compose.yml").is_file():
    pytest.skip(
        "repo root not available (running inside the container)",
        allow_module_level=True,
    )


def load(path):
    return yaml.safe_load((ROOT / path).read_text())


local = load("docker-compose.yml")
staging = load("docker/staging/docker-compose.yml")


def test_local_stack_has_db_backend_frontend_only():
    assert set(local["services"]) == {"db", "backend", "frontend"}
    assert "db_data" in local["volumes"]
    assert "db_data:/var/lib/postgresql/data" in local["services"]["db"]["volumes"]


def test_local_dependency_order_and_health():
    s = local["services"]
    assert s["backend"]["depends_on"]["db"]["condition"] == "service_healthy"
    assert s["frontend"]["depends_on"]["backend"]["condition"] == "service_healthy"
    assert "healthcheck" in s["db"]


def test_local_build_contexts_point_at_existing_dockerfiles():
    s = local["services"]
    be = s["backend"]["build"]
    assert (ROOT / be["context"] / be["dockerfile"]).is_file()
    assert (ROOT / s["frontend"]["build"]["context"] / "Dockerfile").is_file()


def test_local_secrets_come_from_env_not_literals():
    text = (ROOT / "docker-compose.yml").read_text()
    assert "${POSTGRES_PASSWORD:?" in text
    assert "${SECRET_KEY:?" in text
    assert "${HEALTH_CHECK_PASSWORD:?" in text
    env = local["services"]["backend"]["environment"]
    assert env["DEBUG"] == "True"
    assert "redis" not in str(local["services"]).lower()


def test_frontend_api_url_uses_host_port_not_container_name():
    url = local["services"]["frontend"]["environment"]["VITE_API_URL"]
    assert url.startswith("http://localhost:")
    assert "backend" not in url


def test_env_example_covers_every_required_variable_and_has_no_secrets():
    text = (ROOT / ".env.example").read_text()
    for name in ("POSTGRES_PASSWORD", "SECRET_KEY", "HEALTH_CHECK_PASSWORD"):
        assert f"{name}=" in text
    assert "ADMIN_PASSWORD=\n" in text
    assert "DEMO_PASSWORD=\n" in text
    assert ".env" in (ROOT / ".gitignore").read_text().split()


def test_makefile_targets_exist():
    text = (ROOT / "Makefile").read_text()
    for target in ("docker-local:", "docker-down:", "docker-logs:", "docker-test:"):
        assert target in text


def test_staging_stack_services_and_settings():
    s = staging["services"]
    assert set(s) == {"db", "redis", "backend", "celery-worker", "celery-beat"}
    env = staging["x-backend-env"]
    assert env["DJANGO_SETTINGS_MODULE"] == "config.settings.staging"
    assert env["CELERY_BROKER_URL"].startswith("redis://redis:")
    assert env["RATELIMIT_CACHE_URL"].startswith("redis://redis:")
    assert "NUM_PROXIES" in env
    for name in ("celery-worker", "celery-beat"):
        assert s[name]["environment"]["RUN_MIGRATIONS"] == "false"
        assert s[name]["command"][:3] == ["celery", "-A", "config"]
    for name in ("backend", "celery-worker", "celery-beat"):
        b = s[name]["build"]
        assert (ROOT / "docker/staging" / b["context"] / b["dockerfile"]).is_file()


def test_celery_beat_schedule_file_is_writable_location():
    command = staging["services"]["celery-beat"]["command"]
    assert command[command.index("-s") + 1].startswith("/tmp/")


def test_staging_requires_secrets_from_env():
    text = (ROOT / "docker/staging/docker-compose.yml").read_text()
    for name in (
        "SECRET_KEY",
        "POSTGRES_PASSWORD",
        "HEALTH_CHECK_PASSWORD",
        "ALLOWED_HOSTS",
    ):
        assert f"${{{name}:?" in text


def test_entrypoint_can_skip_migrations():
    text = (ROOT / "backend/scripts/entrypoint.sh").read_text()
    assert "RUN_MIGRATIONS" in text
