import factory
from factory.django import DjangoModelFactory

from apps.entities.tests.factories import EntitiesFactory
from apps.users.models import (
    Interfaces,
    Modules,
    PasswordResetTokens,
    RolePrivileges,
    Roles,
    RevokedTokens,
    UserPrivilegeOverrides,
    UserRoles,
    Users,
)


class UsersFactory(DjangoModelFactory):
    class Meta:
        model = Users

    EntityId = factory.SubFactory(EntitiesFactory)
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    FirstName = factory.Faker("first_name")
    LastName = factory.Faker("last_name")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "testpassword123!")
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, password=password, **kwargs)


class SuperAdminFactory(UsersFactory):
    IsSuperAdmin = True
    is_staff = True
    is_superuser = True


class ModulesFactory(DjangoModelFactory):
    class Meta:
        model = Modules

    ModuleName = factory.Sequence(lambda n: f"Module {n}")
    ModuleKey = factory.Sequence(lambda n: f"module_{n}")


class InterfacesFactory(DjangoModelFactory):
    class Meta:
        model = Interfaces

    ModuleId = factory.SubFactory(ModulesFactory)
    InterfaceName = factory.Sequence(lambda n: f"Interface {n}")
    InterfaceKey = factory.Sequence(lambda n: f"interface_{n}")


class RolesFactory(DjangoModelFactory):
    class Meta:
        model = Roles

    RoleName = factory.Sequence(lambda n: f"Role {n}")
    RoleKey = factory.Sequence(lambda n: f"role_{n}"[:20])


class RolePrivilegesFactory(DjangoModelFactory):
    class Meta:
        model = RolePrivileges

    RoleId = factory.SubFactory(RolesFactory)
    ModuleId = factory.SubFactory(ModulesFactory)
    InterfaceId = None
    PermissionType = 5  # All


class UserRolesFactory(DjangoModelFactory):
    class Meta:
        model = UserRoles

    UserId = factory.SubFactory(UsersFactory)
    RoleId = factory.SubFactory(RolesFactory)


class UserPrivilegeOverridesFactory(DjangoModelFactory):
    class Meta:
        model = UserPrivilegeOverrides

    UserId = factory.SubFactory(UsersFactory)
    InterfaceId = factory.SubFactory(InterfacesFactory)
    PermissionType = 2  # Read
    OverrideAction = 1  # Grant
