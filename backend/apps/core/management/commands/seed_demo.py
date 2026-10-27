"""Load demo data. Safe to run repeatedly.

Each app may provide ``<app>/seeders.py`` with ``seed(password: str) -> int``.
Seeders run in INSTALLED_APPS order inside one transaction.
"""

import os
from importlib import import_module
from importlib.util import find_spec

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = (
        "Load idempotent demo data (password from env DEMO_PASSWORD). "
        "Refuses to run when DEBUG=False unless --force."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow running when DEBUG=False (production-like settings).",
        )

    @staticmethod
    def _seeder_modules():
        for config in apps.get_app_configs():
            name = f"{config.name}.seeders"
            if find_spec(config.name) and find_spec(name):
                yield name, import_module(name)

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "Refusing to seed demo data when DEBUG=False. Use --force."
            )
        password = os.environ.get("DEMO_PASSWORD")
        if not password:
            raise CommandError("Set the DEMO_PASSWORD environment variable.")

        with transaction.atomic():
            for name, module in self._seeder_modules():
                count = module.seed(password)
                self.stdout.write(f"{name}: {count} record(s) ensured.")
        self.stdout.write(self.style.SUCCESS("Demo data loaded."))
