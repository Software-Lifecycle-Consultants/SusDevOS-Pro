import factory
from factory.django import DjangoModelFactory

from apps.entities.models import Entities, RelatedEntities


class EntitiesFactory(DjangoModelFactory):
    class Meta:
        model = Entities

    EntityName = factory.Sequence(lambda n: f"Entity {n} Ltd")
    EntityType = 1  # Limited Company
    Country = "United Kingdom"
    BaseCurrency = "GBP"
    FiscalYearEndMonth = 3


class RelatedEntitiesFactory(DjangoModelFactory):
    class Meta:
        model = RelatedEntities

    ParentEntityId = factory.SubFactory(EntitiesFactory)
    ChildEntityId = factory.SubFactory(EntitiesFactory)
    RelationshipType = "subsidiary"
