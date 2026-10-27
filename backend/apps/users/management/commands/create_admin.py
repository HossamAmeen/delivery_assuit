"""Create the first Admin account without public registration.

The password is never accepted as a CLI argument and is never printed or logged.
It is read from the ``ADMIN_PASSWORD`` environment variable, or prompted for.
"""

import getpass
import os

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.users.models import User
from apps.users.phone import normalize_phone


class Command(BaseCommand):
    help = (
        "Create the first Admin user (role=admin, staff, superuser). Password comes "
        "from the ADMIN_PASSWORD env var or an interactive prompt."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default=os.environ.get("ADMIN_USERNAME"),
            help="Admin username (defaults to env ADMIN_USERNAME).",
        )
        parser.add_argument("--phone", default=None, help="Optional phone number.")
        parser.add_argument("--email", default="", help="Optional email address.")
        parser.add_argument(
            "--update-password",
            action="store_true",
            help="If the user already exists, reset its password instead of exiting.",
        )

    def _get_password(self):
        password = os.environ.get("ADMIN_PASSWORD")
        if password:
            return password
        if not self._interactive_stdin():
            raise CommandError(
                "No password provided. Set ADMIN_PASSWORD or run interactively."
            )
        first = getpass.getpass("Password: ")
        second = getpass.getpass("Password (again): ")
        if first != second:
            raise CommandError("Passwords do not match.")
        return first

    @staticmethod
    def _interactive_stdin():
        import sys

        return sys.stdin is not None and sys.stdin.isatty()

    def handle(self, *args, **options):
        username = options["username"]
        if not username:
            raise CommandError("--username is required (or set ADMIN_USERNAME).")
        phone = normalize_phone(options["phone"]) or None
        email = options["email"] or ""

        existing = User.all_objects.filter(username=username).first()
        if existing is not None:
            if not options["update_password"]:
                self.stdout.write(
                    f"User '{username}' already exists. No changes made "
                    "(use --update-password to reset the password)."
                )
                return
            if existing.deleted_at is not None:
                raise CommandError(f"User '{username}' is soft-deleted; not modified.")
            password = self._get_password()
            self._validate(password)
            existing.set_password(password)
            existing.save(update_fields=["password", "modified_at"])
            self.stdout.write(f"Password updated for '{username}'.")
            return

        if phone and User.all_objects.filter(phone=phone).exists():
            raise CommandError("A user with this phone number already exists.")

        password = self._get_password()
        self._validate(password)
        with transaction.atomic():
            User.objects.create_superuser(
                username=username, password=password, phone=phone, email=email
            )
        self.stdout.write(self.style.SUCCESS(f"Admin '{username}' created."))

    @staticmethod
    def _validate(password):
        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError("Invalid password: " + " ".join(exc.messages)) from None
