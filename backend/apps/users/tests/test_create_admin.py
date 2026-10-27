from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.users.models import User

STRONG = "Zx9!kLm2#QwErTy"


def run(*args, **kwargs):
    out = StringIO()
    call_command("create_admin", *args, stdout=out, **kwargs)
    return out.getvalue()


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)


@pytest.mark.django_db
def test_creates_admin_from_env_password(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", STRONG)
    out = run("--username", "boss", "--phone", "0100", "--email", "a@b.com")
    user = User.objects.get(username="boss")
    assert user.role == User.Role.ADMIN
    assert user.is_staff and user.is_superuser and user.is_active
    assert user.phone == "0100"
    assert user.check_password(STRONG)
    assert STRONG not in out


@pytest.mark.django_db
def test_username_from_env(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", STRONG)
    monkeypatch.setenv("ADMIN_USERNAME", "envboss")
    call_command("create_admin", username="envboss", stdout=StringIO())
    assert User.objects.filter(username="envboss").exists()


@pytest.mark.django_db
def test_second_run_is_idempotent(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", STRONG)
    run("--username", "boss")
    monkeypatch.setenv("ADMIN_PASSWORD", "Another!Pass123")
    out = run("--username", "boss")
    assert "already exists" in out
    assert User.objects.filter(username="boss").count() == 1
    assert User.objects.get(username="boss").check_password(STRONG)


@pytest.mark.django_db
def test_update_password(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", STRONG)
    run("--username", "boss")
    monkeypatch.setenv("ADMIN_PASSWORD", "Another!Pass123")
    out = run("--username", "boss", "--update-password")
    assert "Password updated" in out
    assert "Another!Pass123" not in out
    assert User.objects.get(username="boss").check_password("Another!Pass123")


@pytest.mark.django_db
def test_no_password_non_interactive_fails():
    with pytest.raises(CommandError, match="No password"):
        run("--username", "boss")
    assert not User.objects.filter(username="boss").exists()


@pytest.mark.django_db
def test_missing_username_fails(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", STRONG)
    with pytest.raises(CommandError, match="username"):
        run()


@pytest.mark.django_db
def test_weak_password_rejected(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "123")
    with pytest.raises(CommandError, match="Invalid password"):
        run("--username", "boss")
    assert not User.objects.filter(username="boss").exists()


@pytest.mark.django_db
def test_duplicate_phone_rejected(monkeypatch):
    User.objects.create_user("other", "x", phone="0100")
    monkeypatch.setenv("ADMIN_PASSWORD", STRONG)
    with pytest.raises(CommandError, match="phone"):
        run("--username", "boss", "--phone", "0100")


@pytest.mark.django_db
def test_soft_deleted_username_not_duplicated(monkeypatch):
    from django.utils import timezone

    u = User.objects.create_user("boss", "x")
    u.deleted_at = timezone.now()
    u.save()
    monkeypatch.setenv("ADMIN_PASSWORD", STRONG)
    out = run("--username", "boss")
    assert "already exists" in out
    assert User.all_objects.filter(username="boss").count() == 1


@pytest.mark.django_db
def test_admin_can_get_jwt(monkeypatch):
    from rest_framework_simplejwt.tokens import RefreshToken

    monkeypatch.setenv("ADMIN_PASSWORD", STRONG)
    run("--username", "boss")
    user = User.objects.get(username="boss")
    from django.contrib.auth import authenticate

    assert authenticate(username="boss", password=STRONG) == user
    assert RefreshToken.for_user(user).access_token
