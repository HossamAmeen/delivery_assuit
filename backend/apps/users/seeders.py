"""Demo users for ``seed_demo``: one active account per role, plus one account in
each non-active status (to demo the pending/deactivated messages)."""

from .models import User

DEMO_USERS = (
    ("demo_admin", User.Role.ADMIN, "Demo Admin", "01000000001"),
    ("demo_manager", User.Role.MANAGER, "Demo Manager", "01000000002"),
    ("demo_driver", User.Role.DRIVER, "Demo Driver", "01000000003"),
    ("demo_trader", User.Role.TRADER, "Demo Trader", "01000000004"),
    ("demo_client", User.Role.CLIENT, "Demo Client", "01000000005"),
    (
        "demo_driver_pending",
        User.Role.DRIVER,
        "Demo Driver (Pending)",
        "01000000006",
        User.Status.PENDING_APPROVAL,
    ),
    (
        "demo_trader_pending",
        User.Role.TRADER,
        "Demo Trader (Pending)",
        "01000000008",
        User.Status.PENDING_APPROVAL,
    ),
    (
        "demo_client_deactivated",
        User.Role.CLIENT,
        "Demo Client (Deactivated)",
        "01000000007",
        User.Status.DEACTIVATED,
    ),
)


def seed(password: str) -> int:
    """Create or update the demo users. Returns the number of users handled."""
    for username, role, full_name, phone, *rest in DEMO_USERS:
        status = rest[0] if rest else User.Status.ACTIVE
        is_admin = role == User.Role.ADMIN
        user, _ = User.all_objects.update_or_create(
            username=username,
            defaults={
                "role": role,
                "full_name": full_name,
                "phone": phone,
                "status": status,
                "is_active": True,
                "is_staff": is_admin,
                "is_superuser": is_admin,
                "deleted_at": None,
            },
        )
        if not user.check_password(password):
            user.set_password(password)
            user.save(update_fields=["password", "modified_at"])
    return len(DEMO_USERS)
