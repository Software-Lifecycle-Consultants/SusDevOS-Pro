from django.core.management import call_command

import pytest

from apps.users.models import Interfaces, Modules

pytestmark = pytest.mark.django_db


def test_seed_modules_retires_api_key_interface():
    module = Modules.objects.create(
        ModuleName="Legacy Entity Management",
        ModuleKey="legacy_entity_management",
    )
    interface = Interfaces.objects.create(
        ModuleId=module,
        InterfaceName="Manage API Keys",
        InterfaceKey="manage_entity_api_keys",
        Status=1,
    )

    call_command("seed_modules", verbosity=0)
    call_command("seed_modules", verbosity=0)

    interface.refresh_from_db()
    assert interface.Status == 4
