import pytest
from rest_framework.test import APIClient

from apps.users.models import User

pytestmark = pytest.mark.django_db

AR = {
    401: "لم يتم تقديم بيانات الاعتماد أو أنها غير صالحة.",
    403: "ليس لديك صلاحية لتنفيذ هذا الإجراء.",
    404: "المورد غير موجود.",
    429: "تم تجاوز حد الطلبات المسموح به.",
    400: "فشل التحقق من صحة البيانات.",
}
EN = {
    401: "Authentication credentials were not provided or are invalid.",
    403: "You do not have permission to perform this action.",
    404: "Resource not found.",
    429: "Request rate limit exceeded.",
    400: "Validation failed.",
}


@pytest.fixture(autouse=True)
def _cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "i18n-tests",
        }
    }
    from django.core.cache import cache

    cache.clear()


def msg(path, lang=None, method="get", **data):
    kwargs = {"HTTP_ACCEPT_LANGUAGE": lang} if lang else {}
    r = getattr(APIClient(), method)(path, data or None, format="json", **kwargs)
    return r, r.json()["message"]


@pytest.mark.urls("common.tests.urls")
@pytest.mark.parametrize(
    ("path", "code"),
    [
        ("/protected/", 401),
        ("/e/denied/", 403),
        ("/e/notfound/", 404),
    ],
)
def test_error_messages_translated(path, code):
    r, ar = msg(path, "ar")
    assert r.status_code == code
    assert ar == AR[code]
    assert r["Content-Language"] == "ar"
    for lang in ("en", None, "fr"):
        _, en = msg(path, lang)
        assert en == EN[code]


@pytest.mark.urls("common.tests.urls")
def test_validation_failed_translated_and_builtin_field_errors():
    r = APIClient().post("/validate/", {}, format="json", HTTP_ACCEPT_LANGUAGE="ar")
    assert r.status_code == 400
    assert r.json()["message"] == AR[400]
    assert r.json()["errors"]["name"] != ["This field is required."]
    r = APIClient().post("/validate/", {}, format="json")
    assert r.json()["message"] == EN[400]
    assert r.json()["errors"]["name"] == ["This field is required."]


@pytest.mark.urls("common.tests.urls")
def test_unknown_route_404_envelope_translated():
    r = APIClient().get("/nope/", HTTP_ACCEPT_LANGUAGE="ar")
    assert r.status_code == 404
    assert r.json()["message"] == AR[404]


@pytest.mark.urls("common.tests.urls")
def test_quality_values_and_regional_codes():
    _, m = msg("/e/notfound/", "ar-EG,en;q=0.5")
    assert m == AR[404]
    _, m = msg("/e/notfound/", "en-US,ar;q=0.5")
    assert m == EN[404]


def test_429_translated(monkeypatch):
    from rest_framework.throttling import SimpleRateThrottle

    monkeypatch.setattr(
        SimpleRateThrottle,
        "THROTTLE_RATES",
        {**SimpleRateThrottle.THROTTLE_RATES, "auth": "1/minute"},
    )
    c = APIClient()
    c.post("/api/v1/auth/token/", {}, format="json")
    r = c.post("/api/v1/auth/token/", {}, format="json", HTTP_ACCEPT_LANGUAGE="ar")
    assert r.status_code == 429
    assert r.json()["message"] == AR[429]


def test_auth_and_health_messages_translated(settings):
    settings.HEALTH_CHECK_PASSWORD = "pw"
    User.objects.create_user("alice", "Zx9!kLm2#QwErTy")
    c = APIClient()
    r = c.post(
        "/api/v1/auth/token/",
        {"username_or_phone": "alice", "password": "bad"},
        format="json",
        HTTP_ACCEPT_LANGUAGE="ar",
    )
    assert r.json()["message"] == "بيانات الاعتماد غير صحيحة."
    r = c.get(
        "/api/v1/health/", HTTP_X_HEALTH_CHECK_TOKEN="pw", HTTP_ACCEPT_LANGUAGE="ar"
    )
    assert r.json()["message"] == "الخدمة تعمل بشكل سليم."
    r = c.get(
        "/api/v1/health/", HTTP_X_HEALTH_CHECK_TOKEN="x", HTTP_ACCEPT_LANGUAGE="ar"
    )
    assert r.status_code == 403
    assert r.json()["message"] == "كلمة مرور فحص الحالة غير صالحة."
    r = c.get("/api/v1/health/", HTTP_X_HEALTH_CHECK_TOKEN="pw")
    assert r.json()["message"] == "Service is healthy."


def test_every_msgid_in_po_has_arabic():
    import re
    from pathlib import Path

    text = (
        Path(__file__).resolve().parents[2] / "locale/ar/LC_MESSAGES/django.po"
    ).read_text()
    pairs = re.findall(r'msgid "(.+)"\nmsgstr "(.*)"', text)
    assert pairs
    assert all(s for _, s in pairs)
