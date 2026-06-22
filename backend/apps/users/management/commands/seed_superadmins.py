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
from django.core.management.base import BaseCommand
from django.conf import settings
from decouple import config


class Command(BaseCommand):
    help = "Create the two SuperAdmin users from environment variables"

    def handle(self, *args, **options):
        from apps.users.models import Users

        superadmins = [
            {
                "email":    config("SUPERADMIN_1_EMAIL",    default="superadmin1@susdevos.com"),
                "username": config("SUPERADMIN_1_USERNAME", default="superadmin1"),
                "password": config("SUPERADMIN_1_PASSWORD", default="ChangeMe!12345"),
            },
            {
                "email":    config("SUPERADMIN_2_EMAIL",    default="superadmin2@susdevos.com"),
                "username": config("SUPERADMIN_2_USERNAME", default="superadmin2"),
                "password": config("SUPERADMIN_2_PASSWORD", default="ChangeMe!67890"),
            },
        ]

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
