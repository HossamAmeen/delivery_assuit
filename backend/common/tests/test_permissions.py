from types import SimpleNamespace

from common.permissions import IsAdminOrReadOnly, IsAdminRole


def req(method="GET", **user):
    u = SimpleNamespace(
        is_authenticated=user.pop("auth", True), is_staff=False, is_superuser=False
    )
    u.__dict__.update(user)
    return SimpleNamespace(method=method, user=u)


def test_is_admin_role():
    p = IsAdminRole()
    assert p.has_permission(req(is_staff=True), None)
    assert p.has_permission(req(is_superuser=True), None)
    assert not p.has_permission(req(), None)
    assert not p.has_permission(req(auth=False, is_staff=True), None)


def test_admin_or_read_only():
    p = IsAdminOrReadOnly()
    assert p.has_permission(req("GET"), None)
    assert not p.has_permission(req("GET", auth=False), None)
    assert not p.has_permission(req("POST"), None)
    assert p.has_permission(req("POST", is_staff=True), None)
