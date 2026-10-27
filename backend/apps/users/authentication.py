from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.settings import api_settings

from .exceptions import AccountDeactivated, AccountPending, AccountRejected
from .models import User


def _is_integer_id(value) -> bool:
    """simplejwt stores the id as a string; accept an int or a plain digit string."""
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    return (
        isinstance(value, str)
        and value.isascii()
        and value.isdigit()
        and len(value) <= 18
    )


class StatusCheckingJWTAuthentication(JWTAuthentication):
    """JWT auth that re-checks the account status on every request.

    A valid token of an account that is no longer active is refused with 403
    and a machine-readable ``code`` (not 401, so the client can show a screen).
    """

    def get_user(self, validated_token):
        # A signed token whose user id is not an integer must be a clean 401,
        # not a database ValueError (VULN-014).
        user_id = validated_token.get(api_settings.USER_ID_CLAIM)
        if not _is_integer_id(user_id):
            raise InvalidToken("Token contained no recognizable user identification")
        user = super().get_user(validated_token)
        if user.status == User.Status.DEACTIVATED:
            raise AccountDeactivated()
        if user.status == User.Status.PENDING_APPROVAL:
            raise AccountPending()
        if user.status == User.Status.REJECTED:
            raise AccountRejected(user.rejection_reason)
        return user
