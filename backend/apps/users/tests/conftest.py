import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.models import User

PASSWORD = "Zx9!kLm2#QwErTy"


def make_user(username, role, phone, status="active", **extra):
    return User.objects.create_user(
        username,
        PASSWORD,
        phone=phone,
        role=role,
        status=status,
        is_staff=role == "admin",
        full_name=extra.pop("full_name", username.title()),
        **extra,
    )


def client_for(user):
    c = APIClient()
    r = c.post(
        reverse("token"),
        {"username_or_phone": user.username or user.phone, "password": PASSWORD},
        format="json",
    )
    assert r.status_code == 200, r.content
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['data']['access']}")
    return c


@pytest.fixture
def admin(db):
    return make_user("admin1", "admin", "01000000001")


@pytest.fixture
def manager(db):
    return make_user("manager1", "manager", "01000000002")


@pytest.fixture
def admin_client(admin):
    return client_for(admin)


@pytest.fixture
def manager_client(manager):
    return client_for(manager)
