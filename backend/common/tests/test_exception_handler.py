import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.urls("common.tests.urls")


@pytest.fixture
def client():
    return APIClient(raise_request_exception=False)


def body(r):
    return r.json()


def test_validation_error_envelope(client):
    r = client.post("/validate/", {"nested": ["a"]}, format="json")
    assert r.status_code == 400
    d = body(r)
    assert d["success"] is False and d["message"] == "Validation failed."
    assert d["errors"]["name"] == ["This field is required."]
    assert "nested" in d["errors"]


def test_non_field_validation_error(client):
    r = client.post("/validate/", [1], format="json")
    assert r.status_code == 400
    assert "non_field_errors" in body(r)["errors"]


@pytest.mark.parametrize("path", ["/e/notfound/", "/e/http404/", "/nope/"])
def test_not_found(client, path):
    r = client.get(path)
    assert r.status_code == 404
    assert body(r) == {"success": False, "message": "Resource not found.", "errors": {}}


@pytest.mark.parametrize("path", ["/e/denied/", "/e/django-denied/"])
def test_permission_denied(client, path):
    r = client.get(path)
    assert r.status_code == 403
    assert body(r)["message"] == "You do not have permission to perform this action."
    assert body(r)["errors"] == {}


def test_unauthenticated_returns_401(client):
    r = client.get("/protected/")
    assert r.status_code == 401
    assert body(r) == {
        "success": False,
        "message": "Authentication credentials were not provided or are invalid.",
        "errors": {},
    }


def test_method_not_allowed(client):
    r = client.post("/ok/")
    assert r.status_code == 405
    assert body(r)["message"] == "Method not allowed."


def test_parse_error(client):
    r = client.post("/validate/", "{bad", content_type="application/json")
    assert r.status_code == 400
    assert body(r)["success"] is False


def test_custom_application_error(client):
    r = client.get("/e/app/")
    assert r.status_code == 400
    assert body(r) == {
        "success": False,
        "message": "Custom failure.",
        "errors": {"f": ["bad"]},
    }
    r = client.get("/e/conflict/")
    assert r.status_code == 409
    assert body(r)["success"] is False


def test_unexpected_error_does_not_leak(client):
    r = client.get("/e/boom/")
    assert r.status_code == 500
    assert body(r) == {
        "success": False,
        "message": "An unexpected error occurred.",
        "errors": {},
    }
    assert "passwd" not in r.content.decode() and "Traceback" not in r.content.decode()


def test_success_envelope(client):
    assert body(client.get("/ok/")) == {
        "success": True,
        "message": "Hello.",
        "data": {"x": 1},
    }
    assert body(client.get("/empty/"))["data"] == {}


def test_envelope_renderer():
    from rest_framework.response import Response

    from common.responses import EnvelopeJSONRenderer

    class R:
        status_code = 200

    out = EnvelopeJSONRenderer().render({"a": 1}, "application/json", {"response": R()})
    assert b'"success": true' in out.replace(b":", b": ") or b'"success":true' in out
    done = EnvelopeJSONRenderer().render({"success": False}, None, {"response": R()})
    assert b'"data"' not in done
    assert Response  # keep import used


@pytest.mark.urls("config.urls")
def test_default_urlconf_unknown_route_json_and_handlers(client, rf):
    from common.views import not_found, server_error

    r = client.get("/api/v1/does-not-exist/")
    assert r.status_code == 404 and body(r)["message"] == "Resource not found."
    r = server_error(rf.get("/"))
    assert r.status_code == 500 and b"unexpected" in r.content
    assert not_found(rf.get("/")).status_code == 404
