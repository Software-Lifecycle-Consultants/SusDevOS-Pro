from django.db import IntegrityError, transaction

import pytest

from apps.entities.models import Entities, EntityLocations, RelatedEntities
from apps.entities.tests.factories import EntitiesFactory, RelatedEntitiesFactory
from apps.shared.tests.factories import LocationsFactory


@pytest.mark.django_db
class TestEntities:
    def test_create_entity(self):
        entity = EntitiesFactory(EntityName="Acme Corp Ltd")
        assert entity.pk is not None
        assert str(entity) == "Acme Corp Ltd"

    def test_audit_defaults(self):
        entity = EntitiesFactory()
        assert entity.Status == 1
        assert entity.BaseCurrency == "GBP"
        assert entity.FiscalYearEndMonth == 3

    def test_parent_entity_self_fk(self):
        parent = EntitiesFactory()
        child = EntitiesFactory(ParentEntityId=parent, OwnershipSharePercent="60.000")
        assert child.ParentEntityId_id == parent.EntityId
        assert parent.subsidiaries.count() == 1

    def test_soft_delete_pattern(self):
        entity = EntitiesFactory()
        entity.Status = 4
        entity.save()
        entity.refresh_from_db()
        assert entity.Status == 4


@pytest.mark.django_db
class TestRelatedEntities:
    def test_unique_pair_constraint(self):
        parent = EntitiesFactory()
        child = EntitiesFactory()
        RelatedEntities.objects.create(ParentEntityId=parent, ChildEntityId=child)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                RelatedEntities.objects.create(ParentEntityId=parent, ChildEntityId=child)

    def test_cascade_delete(self):
        rel = RelatedEntitiesFactory()
        parent_id = rel.ParentEntityId_id
        Entities.objects.filter(EntityId=parent_id).delete()
        assert RelatedEntities.objects.filter(id=rel.id).count() == 0


@pytest.mark.django_db
class TestEntityLocations:
    def test_link_location(self):
        entity = EntitiesFactory()
        location = LocationsFactory()
        link = EntityLocations.objects.create(EntityId=entity, LocationId=location)
        assert entity.entity_locations.count() == 1
        assert link.pk is not None

    def test_unique_entity_location(self):
        entity = EntitiesFactory()
        location = LocationsFactory()
        EntityLocations.objects.create(EntityId=entity, LocationId=location)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                EntityLocations.objects.create(EntityId=entity, LocationId=location)
