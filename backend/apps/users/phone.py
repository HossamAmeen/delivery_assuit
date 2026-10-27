"""Phone number helpers shared by registration, login and management commands."""

import re
import unicodedata

PHONE_MIN_DIGITS = 8
PHONE_MAX_DIGITS = 15


def normalize_phone(value: str | None) -> str:
    """Return ``value`` reduced to ASCII digits only.

    Accepts spaces, dashes, ``+``, parentheses and Arabic-Indic / Extended
    Arabic-Indic digits (and any other Unicode decimal digit). Anything that is
    not a digit is dropped. ``None`` or blank input gives ``""``.
    """
    if not value:
        return ""
    digits = []
    for char in str(value):
        if char.isdecimal():
            digits.append(str(unicodedata.digit(char)))
    return "".join(digits)


def is_valid_phone(value: str | None) -> bool:
    """True if ``value`` normalises to 8-15 digits."""
    normalized = normalize_phone(value)
    return bool(
        re.fullmatch(rf"\d{{{PHONE_MIN_DIGITS},{PHONE_MAX_DIGITS}}}", normalized)
    )


_PHONE_LIKE = re.compile(r"[\d\s+\-()]+")


def looks_like_phone(value: str | None) -> bool:
    """True when ``value`` is only digits and phone punctuation and is 8-15 digits.

    A username that merely contains digits ("driver2") is not a phone.
    """
    if not value or not _PHONE_LIKE.fullmatch(value.strip()):
        return False
    return is_valid_phone(value)


def is_phone_like(value: str | None) -> bool:
    """True when every character is a digit (any script), space, dash, ``+`` or bracket.

    This is the login rule (VULN-016): such an identifier is treated as a phone,
    anything else is an exact username. It does not check the length.
    """
    return bool(value) and _PHONE_LIKE.fullmatch(value.strip()) is not None
