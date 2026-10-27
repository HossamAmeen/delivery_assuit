"""Checks for the local Docker files. Docker itself is not run (PO decision 2026-10-08)."""

import importlib.util
import os
import socket
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
DOCKERFILE = (ROOT / "docker/local/Dockerfile").read_text()


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


db_ready = load("db_ready")
healthcheck = load("healthcheck")


# --- Dockerfile / .dockerignore -------------------------------------------------


def test_dockerfile_runs_as_non_root_with_entrypoint_and_healthcheck():
    assert DOCKERFILE.startswith("#") or "FROM python:3.13-slim" in DOCKERFILE
    assert "FROM python:3.13-slim" in DOCKERFILE
    assert "requirements/development.txt" in DOCKERFILE
    lines = [line.strip() for line in DOCKERFILE.splitlines()]
    assert "USER app" in lines
    assert any(line.startswith("HEALTHCHECK") for line in lines)
    assert any("scripts/healthcheck.py" in line for line in lines)
    assert any(
        line.startswith("ENTRYPOINT") and "entrypoint.sh" in line for line in lines
    )


def test_dockerfile_bakes_in_no_secrets():
    for forbidden in ("SECRET_KEY", "PASSWORD", "TOKEN", "COPY .env", "ADD .env"):
        assert forbidden not in DOCKERFILE.replace("HEALTH_CHECK_PASSWORD from", "")


def test_dockerignore_excludes_secrets_and_junk():
    entries = (ROOT / ".dockerignore").read_text().split()
    for needed in (".env", "*.sqlite3", ".venv", "__pycache__", ".git"):
        assert needed in entries


def test_dev_requirements_include_postgres_driver():
    assert "psycopg" in (ROOT / "requirements/development.txt").read_text()


# --- shell scripts ---------------------------------------------------------------


@pytest.mark.parametrize("name", ["entrypoint.sh", "wait_for_db.sh"])
def test_shell_scripts_are_strict_executable_and_valid(name):
    path = SCRIPTS / name
    text = path.read_text()
    assert text.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in text
    assert os.access(path, os.X_OK)
    subprocess.run(["bash", "-n", str(path)], check=True)


def test_entrypoint_waits_migrates_then_execs():
    text = (SCRIPTS / "entrypoint.sh").read_text()
    assert (
        text.index("wait_for_db.sh")
        < text.index("migrate --noinput")
        < text.index('exec "$@"')
    )


def test_wait_for_db_script_succeeds_for_sqlite():
    env = {
        **os.environ,
        "DATABASE_URL": "sqlite:///db.sqlite3",
        "DB_WAIT_TIMEOUT": "3",
        "PYTHON": sys.executable,
    }
    result = subprocess.run(
        ["bash", str(SCRIPTS / "wait_for_db.sh")],
        env=env,
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0
    assert "ready" in result.stdout


def test_wait_for_db_script_times_out_and_does_not_leak_the_password():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]  # closed again on exit: nothing listens here
    env = {
        **os.environ,
        "DATABASE_URL": f"postgres://u:s3cretPW@127.0.0.1:{port}/db",
        "DB_WAIT_TIMEOUT": "2",
        "PYTHON": sys.executable,
    }
    result = subprocess.run(
        ["bash", str(SCRIPTS / "wait_for_db.sh")],
        env=env,
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 1
    assert "s3cretPW" not in result.stdout + result.stderr


# --- db_ready --------------------------------------------------------------------


def test_db_ready_unset_and_sqlite_need_no_network():
    assert db_ready.database_ready(None)
    assert db_ready.database_ready("sqlite:///x.db")


def test_db_ready_true_when_port_listens_false_otherwise():
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen()
        port = server.getsockname()[1]
        assert db_ready.database_ready(f"postgres://u:p@127.0.0.1:{port}/d")
    assert not db_ready.database_ready(
        f"postgres://u:p@127.0.0.1:{port}/d", timeout=0.5
    )


def test_db_ready_false_for_unusable_url():
    assert not db_ready.database_ready("postgres:///nohost")


# --- healthcheck -----------------------------------------------------------------


def test_healthcheck_sends_token_header_and_reports_200():
    response = mock.MagicMock(status=200)
    response.__enter__.return_value = response
    with mock.patch("urllib.request.urlopen", return_value=response) as urlopen:
        assert healthcheck.check(port="8000", token="pw")
    request = urlopen.call_args.args[0]
    assert request.full_url == "http://127.0.0.1:8000/api/v1/health/"
    assert request.get_header("X-health-check-token") == "pw"


def test_healthcheck_fails_on_error_and_never_prints_token(capsys):
    with mock.patch("urllib.request.urlopen", side_effect=OSError("refused")):
        assert not healthcheck.check(port="8000", token="topsecret")
    out = capsys.readouterr()
    assert "topsecret" not in out.out + out.err
