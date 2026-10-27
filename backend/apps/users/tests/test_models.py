import pytest
from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError

from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_auth_user_model_is_custom():
    assert get_user_model() is User


def test_create_user_defaults():
    user = User.objects.create_user("ali", "pass12345")
    assert user.role == User.Role.CLIENT
    assert user.is_active and not user.is_staff and not user.is_superuser
    assert user.phone is None and user.email == ""
    assert user.check_password("pass12345")
    assert str(user) == "ali"


def test_create_user_requires_username():
    with pytest.raises(ValueError):
        User.objects.create_user("", "pass12345")


def test_email_is_optional_and_normalized():
    user = User.objects.create_user("a", "p", email="X@EXAMPLE.COM")
    assert user.email == "X@example.com"
    User.objects.create_user("b", "p")
    User.objects.create_user("c", "p")


def test_username_unique():
    User.objects.create_user("ali", "p")
    with pytest.raises(IntegrityError):
        User.objects.create_user("ali", "p")


def test_phone_unique_but_blank_allowed_many_times():
    User.objects.create_user("a", "p", phone="0100")
    with pytest.raises(IntegrityError):
        User.objects.create_user("b", "p", phone="0100")


def test_blank_phones_do_not_collide():
    User.objects.create_user("a", "p", phone="")
    User.objects.create_user("b", "p", phone="")
    assert User.objects.filter(phone__isnull=True).count() == 2


def test_create_superuser_is_admin():
    admin = User.objects.create_superuser("root", "pass12345")
    assert admin.role == User.Role.ADMIN
    assert admin.is_staff and admin.is_superuser


@pytest.mark.parametrize("flag", ["is_staff", "is_superuser"])
def test_create_superuser_rejects_false_flags(flag):
    with pytest.raises(ValueError):
        User.objects.create_superuser("root", "p", **{flag: False})


def test_soft_delete_hides_user_and_blocks_login():
    user = User.objects.create_user("ali", "pass12345")
    assert authenticate(username="ali", password="pass12345") == user
    user.soft_delete()
    assert not User.objects.filter(pk=user.pk).exists()
    assert User.all_objects.filter(pk=user.pk).exists()
    assert authenticate(username="ali", password="pass12345") is None
    user.restore()
    assert User.objects.filter(pk=user.pk).exists()


def test_roles_use_driver_naming():
    assert {r.label for r in User.Role} == {
        "Admin",
        "Manager",
        "Driver",
        "Trader",
        "Client",
    }


def test_status_defaults_to_active_and_is_operational():
    user = User.objects.create_user("ali", "pass12345")
    assert user.status == User.Status.ACTIVE
    assert user.is_operational


@pytest.mark.parametrize("status", ["pending_approval", "deactivated"])
def test_non_active_status_is_not_operational(status):
    user = User.objects.create_user("ali", "pass12345", status=status)
    assert not user.is_operational


def test_soft_deleted_user_is_not_operational():
    user = User.objects.create_user("ali", "pass12345")
    user.soft_delete()
    assert not User.all_objects.get(pk=user.pk).is_operational


def test_phone_is_normalised_on_create():
    user = User.objects.create_user("ali", "p", phone="+20 100-123-4567")
    assert user.phone == "201001234567"


def test_username_is_optional_but_unique():
    a = User.objects.create_user("a", "p", phone="01000000001")
    a.username = None
    a.save()
    b = User.objects.create_user("b", "p", phone="01000000002")
    b.username = None
    b.save()
    assert str(a) == "01000000001"


def test_login_by_unnormalised_phone():
    from apps.users.services import authenticate_user

    user = User.objects.create_user("ali", "pass12345", phone="01001234567")
    assert authenticate_user("0100 123-4567", "pass12345") == user
