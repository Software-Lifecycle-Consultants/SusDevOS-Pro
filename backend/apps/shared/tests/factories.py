import factory
from factory.django import DjangoModelFactory

from apps.shared.models import (
    Contacts,
    DocumentTags,
    Documents,
    EntityApiKeys,
    ImageTags,
    Images,
    Locations,
    Tags,
)

# Default tenant id used across shared factories (EntityId is a bare int here).
DEFAULT_ENTITY_ID = 1


class LocationsFactory(DjangoModelFactory):
    class Meta:
        model = Locations

    Title = factory.Sequence(lambda n: f"Location {n}")
    City = "London"
    Country = "United Kingdom"


class TagsFactory(DjangoModelFactory):
    class Meta:
        model = Tags

    EntityId = DEFAULT_ENTITY_ID
    TagName = factory.Sequence(lambda n: f"Tag {n}")


class ContactsFactory(DjangoModelFactory):
    class Meta:
        model = Contacts

    EntityId = DEFAULT_ENTITY_ID
    Name = factory.Faker("name")
    Email = factory.Faker("email")
    ModuleKey = "projects"


class DocumentsFactory(DjangoModelFactory):
    class Meta:
        model = Documents

    EntityId = DEFAULT_ENTITY_ID
    DocTitle = factory.Sequence(lambda n: f"Document {n}")
    DocPath = factory.Sequence(lambda n: f"node-1/1/projects/1/{n}.pdf")
    DocType = "application/pdf"
    ModuleKey = "projects"


class ImagesFactory(DjangoModelFactory):
    class Meta:
        model = Images

    EntityId = DEFAULT_ENTITY_ID
    ImagePath = factory.Sequence(lambda n: f"node-1/1/projects/1/{n}.jpg")
    ModuleKey = "projects"


class EntityApiKeysFactory(DjangoModelFactory):
    class Meta:
        model = EntityApiKeys

    EntityId = DEFAULT_ENTITY_ID
    HashedApiKey = factory.Sequence(lambda n: f"{n:064d}")
    KeyPrefix = factory.Sequence(lambda n: f"sk_{n:04d}"[:8])


class DocumentTagsFactory(DjangoModelFactory):
    class Meta:
        model = DocumentTags

    DocumentId = factory.SubFactory(DocumentsFactory)
    TagId = factory.SubFactory(TagsFactory)


class ImageTagsFactory(DjangoModelFactory):
    class Meta:
        model = ImageTags

    ImageId = factory.SubFactory(ImagesFactory)
    TagId = factory.SubFactory(TagsFactory)
