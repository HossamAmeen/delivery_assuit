from typing import ClassVar

import pytest
from django.urls import path, reverse
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from apps.users.models import User
from apps.users.permissions import (
    IsAdmin,
    IsAdminOrManager,
    IsClient,
    IsDriver,
    IsOperational,
    IsTrader,
    can_manage_account,
)
from config.urls import urlpatterns as base_urls

pytestmark = pytest.mark.django_db
PW = "Zx9!kLm2#QwErTy"
ROLES = ["admin", "manager", "driver", "trader", "client"]


def _view(perm):
    class V(APIView):
        permission_classes: ClassVar[list] = [perm]

        def get(self, request):
            return Response({"success": True, "message": "ok", "data": {}})

    return V.as_view()


urlpatterns = [
    path("t/admin/", _view(IsAdmin)),
    path("t/staff/", _view(IsAdminOrManager)),
    path("t/driver/", _view(IsDriver)),
    path("t/trader/", _view(IsTrader)),
    path("t/client/", _view(IsClient)),
    path("t/operational/", _view(IsOperational)),
    *base_urls,
]

ALLOWED = {
    "admin": {"admin"},
    "staff": {"admin", "manager"},
    "driver": {"driver"},
    "trader": {"trader"},
    "client": {"client"},
    "operational": set(ROLES),
}


@pytest.fixture(autouse=True)
def _urls(settings):
    settings.ROOT_URLCONF = __name__
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "perm-tests",
        }
    }
    from django.core.cache import cache

    cache.clear()


def make(role, **kw):
    return User.objects.create_user(
        f"{role}-{User.all_objects.count()}", PW, role=role, **kw
    )


def auth(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return c


@pytest.mark.parametrize("action", list(ALLOWED))
@pytest.mark.parametrize("role", ROLES)
def test_role_matrix(role, action):
    r = auth(make(role)).get(f"/t/{action}/")
    if role in ALLOWED[action]:
        assert r.status_code == 200
    else:
        assert r.status_code == 403
        body = r.json()
        assert body["success"] is False
        assert body["message"] == "You do not have permission to perform this action."


@pytest.mark.parametrize("action", list(ALLOWED))
def test_anonymous_gets_401(action):
    r = APIClient().get(f"/t/{action}/")
    assert r.status_code == 401
    assert r.json()["success"] is False


def test_pending_account_token_is_refused_everywhere():
    user = make("driver", status="pending_approval")
    r = auth(user).get("/t/operational/")
    assert r.status_code == 403
    assert r.json()["code"] == "account_pending"


def test_is_operational_denies_non_active_user_object():
    class Req:
        user = User(status="pending_approval", role="client")

    assert IsOperational().has_permission(Req(), None) is False
    assert IsClient().has_permission(Req(), None) is False


@pytest.mark.parametrize(
    ("actor", "target", "expected"),
    [
        ("admin", "admin", True),
        ("admin", "manager", True),
        ("admin", "client", True),
        ("manager", "admin", False),
        ("manager", "manager", True),
        ("manager", "driver", True),
        ("manager", "trader", True),
        ("manager", "client", True),
        ("driver", "client", False),
        ("trader", "driver", False),
        ("client", "client", False),
    ],
)
def test_can_manage_account(actor, target, expected):
    assert can_manage_account(make(actor), make(target)) is expected


def test_can_manage_account_rejects_anonymous_and_inactive():
    from django.contrib.auth.models import AnonymousUser

    target = make("client")
    assert can_manage_account(None, target) is False
    assert can_manage_account(AnonymousUser(), target) is False
    inactive = make("admin", status="deactivated")
    assert can_manage_account(inactive, target) is False


def test_me_returns_profile():
    user = make("driver", phone="0100 123 4567", full_name="Ahmed Ali")
    r = auth(user).get(reverse("me"))
    assert r.status_code == 200
    data = r.json()["data"]["user"]
    assert data == {
        "id": user.id,
        "full_name": "Ahmed Ali",
        "phone": "01001234567",
        "username": user.username,
        "email": "",
        "role": "driver",
        "status": "active",
        "rejection_reason": "",
    }
    assert "password" not in data


def test_me_unauthenticated_401_envelope():
    r = APIClient().get(reverse("me"))
    assert r.status_code == 401
    body = r.json()
    assert body["success"] is False
    assert "errors" in body


def test_me_deactivated_after_token_issued_403_with_code():
    user = make("client")
    c = auth(user)
    user.status = "deactivated"
    user.save()
    r = c.get(reverse("me"))
    assert r.status_code == 403
    body = r.json()
    assert body["code"] == "account_deactivated"
    assert body["success"] is False


def test_me_soft_deleted_user_gets_401():
    user = make("client")
    c = auth(user)
    user.deleted_at = "2020-01-01T00:00:00Z"
    user.save()
    assert c.get(reverse("me")).status_code == 401


def test_me_post_not_allowed():
    assert auth(make("client")).post(reverse("me")).status_code == 405
