import hashlib
import logging
import secrets
from datetime import timedelta
from functools import lru_cache

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import IntegrityError, OperationalError, transaction
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import (
    TokenBackendError,
    TokenBackendExpiredToken,
    TokenError,
)
from rest_framework_simplejwt.state import token_backend
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from .exceptions import AccountDeactivated, AccountPending, AccountRejected
from .models import PasswordResetToken, User
from .phone import is_phone_like, looks_like_phone, normalize_phone

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _dummy_hash() -> str:
    """A hash made with the current default hasher, used to equalise timing."""
    return make_password("timing-equaliser-not-a-real-password")


def authenticate_user(identifier: str, password: str) -> User | None:
    """Return the active user matching username or phone and password, else None.

    Unknown, wrong password, inactive and soft-deleted all give None so callers
    cannot distinguish them (no account enumeration). A password hash is always
    computed, so response time does not reveal whether the account exists.
    """
    identifier = identifier.strip()
    # An exact username match wins. Only a phone-like identifier is normalised
    # to a phone, so "x01000000005" never logs in as phone 01000000005 (VULN-016).
    user = User.objects.filter(username=identifier).first()
    if user is None and is_phone_like(identifier):
        phone = normalize_phone(identifier)
        user = User.objects.filter(phone=phone).first() if phone else None
    if user is None:
        check_password(password, _dummy_hash())
        return None
    password_ok = user.check_password(password)
    if not password_ok or not user.is_active:
        return None
    return user


def ensure_can_login(user: User) -> None:
    """Refuse a non-active account. Call ONLY after the password was verified,
    so the status is never revealed to someone who does not know the password."""
    if user.status == User.Status.PENDING_APPROVAL:
        raise AccountPending()
    if user.status == User.Status.DEACTIVATED:
        raise AccountDeactivated()
    if user.status == User.Status.REJECTED:
        raise AccountRejected(user.rejection_reason)


# Self-registration: role comes from the endpoint, status from the role.
REGISTRATION_STATUS = {
    User.Role.DRIVER: User.Status.PENDING_APPROVAL,
    User.Role.TRADER: User.Status.PENDING_APPROVAL,
    User.Role.CLIENT: User.Status.ACTIVE,
}

PHONE_TAKEN = _("A user with this phone number already exists.")
RESET_LINK_INVALID = _("This reset link is invalid or has expired.")
EMAIL_TAKEN = _("A user with this email already exists.")
CURRENT_PASSWORD_WRONG = _("Current password is incorrect.")


def phone_exists(phone: str, *, exclude_pk: int | None = None) -> bool:
    """True if any account (even soft-deleted, the DB constraint covers it) has it."""
    return User.all_objects.filter(phone=phone).exclude(pk=exclude_pk).exists()


def email_exists(email: str, *, exclude_pk: int | None = None) -> bool:
    return User.objects.filter(email__iexact=email).exclude(pk=exclude_pk).exists()


def _taken_errors(phone: str, email: str) -> dict:
    if email and email_exists(email):
        return {"email": [EMAIL_TAKEN]}
    return {"phone": [PHONE_TAKEN]}


def register_account(
    *, role: str, full_name: str, phone: str, password: str, email: str = ""
) -> User:
    """Create a self-registered account. ``phone`` must already be normalised.

    Raises ``ValidationError`` (field errors) if the phone was taken concurrently.
    """
    if role not in REGISTRATION_STATUS:
        raise ValueError(f"Role {role!r} cannot self-register.")
    try:
        with transaction.atomic():
            user = User.objects.create_account(
                phone,
                password,
                full_name=full_name,
                email=email,
                role=role,
                status=REGISTRATION_STATUS[role],
            )
        # Imported here: the notifications app depends on the users app, not the reverse.
        from apps.notifications import services as notifications

        notifications.on_account_registered(user)
        return user
    except IntegrityError:
        # Lost a race with another request using the same phone or email.
        raise ValidationError(_taken_errors(phone, email)) from None


class _TokenReused(Exception):
    """The refresh token was already blacklisted. Raised inside ``atomic()`` so
    the failed claim rolls back, then handled outside it."""


def revoke_refresh_family(user_id: int) -> None:
    """Blacklist every outstanding refresh token of this user (VULN-017)."""
    rows = OutstandingToken.objects.filter(user_id=user_id)
    for row in rows:
        BlacklistedToken.objects.get_or_create(token=row)


def revoke_family_if_blacklisted(raw_refresh: str) -> None:
    """If ``raw_refresh`` is a still-signed, already-blacklisted refresh token,
    blacklist the rest of that user's refresh tokens. Expired or forged values
    are ignored."""
    try:
        payload = token_backend.decode(raw_refresh, verify=True)
    except (TokenBackendExpiredToken, TokenBackendError):
        return
    if payload.get("token_type") != "refresh":
        return
    jti = payload.get("jti")
    user_id = payload.get("user_id")
    if not jti or user_id is None:
        return
    if not BlacklistedToken.objects.filter(token__jti=jti).exists():
        return
    revoke_refresh_family(int(user_id))


def rotate_refresh_token(raw_refresh: str) -> dict[str, str]:
    """Exchange a refresh token for a new access + refresh pair.

    The old refresh token is blacklisted (rotation). Raises ``TokenError`` if the
    token is invalid, expired, blacklisted, or its account is not operational
    (deactivated, pending approval, rejected, or soft-deleted).

    Reuse of an already-blacklisted refresh token also blacklists every other
    outstanding refresh token of that user (VULN-017).
    """
    try:
        # Reads below can also hit a lock while a competing rotation is writing.
        token = RefreshToken(raw_refresh)  # verifies signature, expiry and blacklist
    except TokenError:
        revoke_family_if_blacklisted(raw_refresh)
        raise
    try:
        user = User.objects.filter(pk=token.get("user_id")).first()
        if user is None or not user.is_active or not user.is_operational:
            raise TokenError("Account is not operational.")
        with transaction.atomic():
            # Single-use at the database level (VULN-011). Lock the outstanding row
            # (a no-op on SQLite, which serialises writers anyway), then claim the
            # token by creating its BlacklistedToken row; the unique constraint
            # means exactly one concurrent caller gets created=True. Everyone else
            # sees an existing row and is refused. The new pair is only issued
            # after the claim, inside the same transaction.
            OutstandingToken.objects.select_for_update().filter(
                jti=token["jti"]
            ).first()
            _, created = token.blacklist()
            if not created:
                # Roll this claim back, then revoke the family outside the block.
                raise _TokenReused()
            new_refresh = RefreshToken.for_user(user)
    except _TokenReused:
        revoke_family_if_blacklisted(raw_refresh)
        raise TokenError("Token is blacklisted.") from None
    except OperationalError as exc:
        # Lock timeout / deadlock / "database is locked": the caller lost the race
        # or the DB is busy. Refuse cleanly (401) instead of a raw 500; no new pair
        # was issued because the transaction rolled back.
        raise TokenError("Token could not be rotated.") from exc
    return {"access": str(new_refresh.access_token), "refresh": str(new_refresh)}


def logout(raw_refresh: str) -> None:
    """Blacklist a refresh token. Idempotent.

    Already blacklisted or expired (but genuinely signed) refresh tokens are
    accepted silently. Raises ``TokenError`` when the value is not a refresh token.
    """
    try:
        RefreshToken(raw_refresh).blacklist()
        return
    except TokenError:
        pass
    # Not usable: decide between "already dead" (fine) and "not a token" (error).
    try:
        payload = token_backend.decode(raw_refresh, verify=True)
    except TokenBackendExpiredToken:
        return
    except TokenBackendError as exc:
        raise TokenError("Invalid token.") from exc
    if payload.get("token_type") != "refresh":
        raise TokenError("Invalid token.")


def change_password(user: User, *, current_password: str, new_password: str) -> None:
    """Change the caller's own password and revoke all their refresh tokens.

    Raises ``ValidationError`` (field errors) when the current password is wrong
    or the new one fails the shared validators. Nothing is saved in that case.
    """
    if not user.check_password(current_password):
        raise ValidationError({"current_password": [CURRENT_PASSWORD_WRONG]})
    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as exc:
        raise ValidationError({"new_password": list(exc.messages)}) from exc
    with transaction.atomic():
        user.set_password(new_password)
        user.save(update_fields=["password"])
        revoke_refresh_family(user.pk)


def update_profile(user: User, **changes) -> User:
    """Update the caller's own name, phone, and email. Values are already cleaned.

    Raises ``ValidationError`` if a concurrent request took the phone or email.
    """
    if not changes:
        return user
    try:
        with transaction.atomic():
            for field, value in changes.items():
                setattr(user, field, value)
            user.save(update_fields=[*changes, "modified_at"])
    except IntegrityError:
        user.refresh_from_db()
        raise ValidationError(
            _taken_errors(changes.get("phone", ""), changes.get("email", ""))
        ) from None
    return user


# --- Password recovery (TASK-048) ---------------------------------------------


def _hash_reset_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def find_user_for_recovery(identifier: str) -> User | None:
    """Match a phone (only if it looks like one), an exact username, or an email.

    Soft-deleted accounts are not found (``User.objects`` hides them).
    """
    identifier = identifier.strip()
    if "@" in identifier:
        return User.objects.filter(email__iexact=identifier).first()
    user = User.objects.filter(username=identifier).first()
    if user is None and looks_like_phone(identifier):
        user = User.objects.filter(phone=normalize_phone(identifier)).first()
    return user


def _reset_email(raw_token: str) -> tuple[str, str]:
    link = f"{settings.FRONTEND_ORIGIN}/reset-password?token={raw_token}"
    minutes = settings.PASSWORD_RESET_TIMEOUT_MINUTES
    subject = gettext("Reset your password")
    body = gettext(
        "We received a request to reset your password.\n\n"
        "Open this link to choose a new password (valid for %(minutes)d minutes, "
        "one use only):\n%(link)s\n\n"
        "If you did not ask for this, ignore this email. Your password stays the same."
    ) % {"minutes": minutes, "link": link}
    return subject, body


def request_password_reset(identifier: str) -> None:
    """Email a single-use reset link when the account exists and has an email.

    Returns nothing in every case, so the caller answers identically. The token
    and the message are built even for an unknown account so the work is alike.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_reset_token(raw_token)
    subject, body = _reset_email(raw_token)
    user = find_user_for_recovery(identifier)
    if user is None or not user.email:
        return
    now = timezone.now()
    with transaction.atomic():
        # A newer request invalidates the previous unused link.
        PasswordResetToken.objects.filter(user=user, used_at__isnull=True).update(
            used_at=now
        )
        PasswordResetToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=now + timedelta(minutes=settings.PASSWORD_RESET_TIMEOUT_MINUTES),
        )
    try:
        send_mail(subject, body, None, [user.email], fail_silently=False)
    except Exception:
        # Do not turn a mail outage into an answer that reveals the account.
        logger.exception("Password reset email could not be sent (user %s)", user.pk)


def _find_valid_reset_token(raw: str) -> PasswordResetToken | None:
    return (
        PasswordResetToken.objects.select_related("user")
        .filter(
            token_hash=_hash_reset_token(raw),
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
            user__deleted_at__isnull=True,
        )
        .first()
    )


def confirm_password_reset(*, token: str, new_password: str) -> None:
    """Set a new password with a valid reset token, once.

    Raises ``ValidationError`` for an unknown, expired or used token, or a weak
    password. A weak password does not burn the token.
    """
    row = _find_valid_reset_token(token)
    if row is None:
        raise ValidationError({"token": [RESET_LINK_INVALID]})
    try:
        validate_password(new_password, user=row.user)
    except DjangoValidationError as exc:
        raise ValidationError({"new_password": list(exc.messages)}) from exc
    with transaction.atomic():
        # Claim the token. Exactly one concurrent caller sees updated == 1.
        claimed = PasswordResetToken.objects.filter(
            pk=row.pk, used_at__isnull=True, expires_at__gt=timezone.now()
        ).update(used_at=timezone.now())
        if not claimed:
            raise ValidationError({"token": [RESET_LINK_INVALID]})
        row.user.set_password(new_password)
        row.user.save(update_fields=["password", "modified_at"])
        PasswordResetToken.objects.filter(user=row.user, used_at__isnull=True).update(
            used_at=timezone.now()
        )
        revoke_refresh_family(row.user.pk)
