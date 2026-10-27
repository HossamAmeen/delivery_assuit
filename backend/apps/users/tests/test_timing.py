"""VULN-002: unknown and existing accounts must both pay for a password hash."""

from unittest import mock

import pytest

from apps.users import services
from apps.users.models import User

pytestmark = pytest.mark.django_db
PW = "Zx9!kLm2#QwErTy"


def test_unknown_user_still_computes_a_hash():
    with mock.patch.object(services, "check_password") as dummy:
        assert services.authenticate_user("ghost", "x") is None
    dummy.assert_called_once()


def test_inactive_user_still_computes_a_hash_and_is_rejected():
    user = User.objects.create_user("idle", PW)
    user.is_active = False
    user.save()
    with mock.patch.object(User, "check_password", return_value=True) as real:
        assert services.authenticate_user("idle", PW) is None
    real.assert_called_once()


def test_valid_user_and_wrong_password():
    User.objects.create_user("alice", PW, phone="0100")
    assert services.authenticate_user("alice", PW).username == "alice"
    assert services.authenticate_user("0100", PW).username == "alice"
    assert services.authenticate_user("alice", "nope") is None


def test_timing_is_comparable():
    import statistics
    import time

    User.objects.create_user("alice", PW)

    def median(ident):
        samples = []
        for _ in range(5):
            start = time.perf_counter()
            services.authenticate_user(ident, "wrong")
            samples.append(time.perf_counter() - start)
        return statistics.median(samples)

    services.authenticate_user("ghost", "x")  # warm the cached dummy hash
    known, unknown = median("alice"), median("ghost")
    assert unknown > known * 0.3  # before the fix this ratio was about 0.006
