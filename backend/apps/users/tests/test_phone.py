import pytest

from apps.users.phone import is_valid_phone, normalize_phone


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0100 123 4567", "01001234567"),
        ("+20 100-123-4567", "201001234567"),
        ("+201001234567", "201001234567"),
        ("(010) 0123-4567", "01001234567"),
        ("٠١٠٠١٢٣٤٥٦٧", "01001234567"),
        ("۰۱۰۰۱۲۳۴۵۶۷", "01001234567"),
        ("+٢٠ 100 123 4567", "201001234567"),
        ("", ""),
        (None, ""),
        ("abc", ""),
    ],
)
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize(
    ("raw", "valid"),
    [
        ("1234567", False),
        ("12345678", True),
        ("1" * 15, True),
        ("1" * 16, False),
        ("", False),
    ],
)
def test_is_valid_phone_bounds(raw, valid):
    assert is_valid_phone(raw) is valid
