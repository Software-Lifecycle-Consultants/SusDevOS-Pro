"""
Management command: seed_superadmins

Creates the two hardcoded SuperAdmin accounts from environment variables.
Safe to run multiple times — uses get_or_create.

Usage:
    python manage.py seed_superadmins

Environment variables required:
    SUPERADMIN_1_EMAIL, SUPERADMIN_1_USERNAME, SUPERADMIN_1_PASSWORD
    SUPERADMIN_2_EMAIL, SUPERADMIN_2_USERNAME, SUPERADMIN_2_PASSWORD
"""
from django.core.management.base import BaseCommand, CommandError

from decouple import UndefinedValueError, config


class Command(BaseCommand):
    help = "Create the two SuperAdmin users from environment variables"

    def handle(self, *args, **options):
        from apps.users.models import Users

        # All six variables are required — no fallback to known strings.
        try:
            superadmins = [
                {
                    "email":    config("SUPERADMIN_1_EMAIL"),
                    "username": config("SUPERADMIN_1_USERNAME"),
                    "password": config("SUPERADMIN_1_PASSWORD"),
                },
                {
                    "email":    config("SUPERADMIN_2_EMAIL"),
                    "username": config("SUPERADMIN_2_USERNAME"),
                    "password": config("SUPERADMIN_2_PASSWORD"),
                },
            ]
        except UndefinedValueError as e:
            raise CommandError(
                f"Missing required environment variable: {e}. "
                "Set all SUPERADMIN_* variables in .env.prod before running this command."
            ) from e

        for sa in superadmins:
            user, created = Users.objects.get_or_create(
                email=sa["email"],
                defaults={
                    "username":     sa["username"],
                    "IsSuperAdmin": True,
                    "is_staff":     True,
                    "is_superuser": True,
                    "is_active":    True,
                },
            )
            if created:
                user.set_password(sa["password"])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created SuperAdmin: {sa['email']}"))
            else:
                self.stdout.write(f"SuperAdmin already exists: {sa['email']}")
