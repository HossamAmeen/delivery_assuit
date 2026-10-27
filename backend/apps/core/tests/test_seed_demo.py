from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.users.models import User

PASSWORD = "Zx9!kLm2#QwErTy"


def run(*args):
    out = StringIO()
    call_command("seed_demo", *args, stdout=out)
    return out.getvalue()


@pytest.fixture(autouse=True)
def _env(monkeypatch, settings):
    monkeypatch.setenv("DEMO_PASSWORD", PASSWORD)
    settings.DEBUG = True


@pytest.mark.django_db
def test_creates_one_user_per_role():
    out = run()
    roles = set(User.objects.values_list("role", flat=True))
    assert roles == {r.value for r in User.Role}
    assert User.objects.get(username="demo_admin").is_superuser
    assert not User.objects.get(username="demo_client").is_staff
    assert User.objects.get(username="demo_driver").check_password(PASSWORD)
    assert PASSWORD not in out


@pytest.mark.django_db
def test_idempotent_row_counts():
    run()
    first = User.all_objects.count()
    run()
    assert User.all_objects.count() == first == 8


@pytest.mark.django_db
def test_second_run_repairs_changed_data_and_restores_deleted():
    run()
    user = User.objects.get(username="demo_manager")
    user.role = User.Role.CLIENT
    user.save()
    User.objects.get(username="demo_driver").soft_delete()
    run()
    assert User.objects.get(username="demo_manager").role == User.Role.MANAGER
    assert User.objects.filter(username="demo_driver").exists()


@pytest.mark.django_db
def test_refuses_when_debug_false(settings):
    settings.DEBUG = False
    with pytest.raises(CommandError, match="DEBUG=False"):
        run()
    assert User.all_objects.count() == 0
    run("--force")
    assert User.all_objects.count() == 8


@pytest.mark.django_db
def test_requires_demo_password(monkeypatch):
    monkeypatch.delenv("DEMO_PASSWORD")
    with pytest.raises(CommandError, match="DEMO_PASSWORD"):
        run()


@pytest.mark.django_db
def test_every_status_and_role_status_combos_represented():
    run()
    # "rejected" is created by test factories, not seeded (TASK-049).
    assert set(User.objects.values_list("status", flat=True)) == {
        s.value for s in User.Status if s != User.Status.REJECTED
    }
    for name in ("demo_driver", "demo_trader"):
        user = User.objects.get(username=name)
        assert user.status == User.Status.ACTIVE and user.is_operational
    pending = User.objects.get(username="demo_driver_pending")
    assert pending.role == User.Role.DRIVER
    assert pending.status == User.Status.PENDING_APPROVAL
    assert not pending.is_operational
    gone = User.objects.get(username="demo_client_deactivated")
    assert gone.role == User.Role.CLIENT
    assert gone.status == User.Status.DEACTIVATED
    assert gone.check_password(PASSWORD)


@pytest.mark.django_db
def test_second_run_restores_status():
    run()
    User.objects.filter(username="demo_driver_pending").update(
        status=User.Status.ACTIVE
    )
    run()
    assert (
        User.objects.get(username="demo_driver_pending").status
        == User.Status.PENDING_APPROVAL
    )
