from django.utils.translation import gettext_lazy as _
from rest_framework import status

from common.exceptions import ApplicationError


class AccountPending(ApplicationError):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _(
        "Your account is pending approval. You will be able to log in once an "
        "administrator approves it."
    )
    default_code = "account_pending"
    public_code = "account_pending"


class AccountDeactivated(ApplicationError):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _(
        "Your account has been deactivated. Please contact the administrator."
    )
    default_code = "account_deactivated"
    public_code = "account_deactivated"


class AccountRejected(ApplicationError):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _("Your registration was rejected.")
    default_code = "account_rejected"
    public_code = "account_rejected"

    def __init__(self, reason: str = ""):
        message = None
        if reason:
            message = _("Your registration was rejected. Reason: %(reason)s.") % {
                "reason": reason
            }
        super().__init__(message=message)


class AdminProtected(ApplicationError):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _("You cannot manage an administrator account.")
    default_code = "admin_protected"
    public_code = "admin_protected"
