import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.urls("common.tests.urls")


def test_default_page_size_and_envelope():
    d = APIClient().get("/list/").json()
    assert d["success"] is True
    assert d["data"]["count"] == 250 and len(d["data"]["results"]) == 20
    assert d["data"]["next"].startswith("http") and d["data"]["previous"] is None


def test_page_size_param_and_max():
    c = APIClient()
    assert len(c.get("/list/?page_size=5").json()["data"]["results"]) == 5
    assert len(c.get("/list/?page_size=500").json()["data"]["results"]) == 100


def test_page_size_from_setting(settings):
    settings.API_PAGE_SIZE = 7
    assert len(APIClient().get("/list/").json()["data"]["results"]) == 7


def test_invalid_page_is_404_envelope():
    r = APIClient().get("/list/?page=99")
    assert r.status_code == 404 and r.json()["success"] is False
