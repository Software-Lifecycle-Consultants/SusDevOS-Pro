import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.shared.models import DocumentTags, ImageTags, Locations, Tags
from apps.shared.tests.factories import (
    ContactsFactory,
    DocumentsFactory,
    EntityApiKeysFactory,
    ImagesFactory,
    LocationsFactory,
    TagsFactory,
)


@pytest.mark.django_db
class TestBaseAuditMixin:
    def test_audit_defaults(self):
        loc = LocationsFactory()
        assert loc.Status == 1
        assert loc.ApprovalStatus == 1
        assert loc.DeletedAt is None
        assert loc.CreatedAt is not None
        assert loc.UpdatedAt is not None
        assert loc.CreatedBy is None

    def test_updated_at_advances_on_save(self):
        loc = LocationsFactory()
        first = loc.UpdatedAt
        loc.Title = "Changed"
        loc.save()
        loc.refresh_from_db()
        assert loc.UpdatedAt >= first


@pytest.mark.django_db
class TestLocations:
    def test_gps_defaults_to_empty_dict(self):
        loc = Locations.objects.create(Title="HQ", City="London", Country="UK")
        assert loc.GPSCoordinates == {}

    def test_str(self):
        loc = LocationsFactory(Title="HQ", City="London", Country="UK")
        assert str(loc) == "HQ (London, UK)"


@pytest.mark.django_db
class TestTags:
    def test_normalized_set_on_save(self):
        tag = Tags.objects.create(EntityId=1, TagName="  Carbon Credits ")
        assert tag.TagNameNormalized == "carbon credits"

    def test_unique_per_entity_case_insensitive(self):
        Tags.objects.create(EntityId=1, TagName="Carbon")
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Tags.objects.create(EntityId=1, TagName="carbon")

    def test_same_name_allowed_for_different_entity(self):
        TagsFactory(EntityId=1, TagName="Carbon")
        other = TagsFactory(EntityId=2, TagName="Carbon")
        assert other.pk is not None


@pytest.mark.django_db
class TestContacts:
    def test_valid_module_key_passes_validation(self):
        contact = ContactsFactory(ModuleKey="emissions")
        contact.full_clean()  # should not raise

    def test_invalid_module_key_rejected(self):
        contact = ContactsFactory.build(ModuleKey="not_a_real_module")
        with pytest.raises(ValidationError):
            contact.full_clean()

    def test_location_set_null_on_delete(self):
        loc = LocationsFactory()
        contact = ContactsFactory(LocationId=loc)
        loc.delete()
        contact.refresh_from_db()
        assert contact.LocationId_id is None


@pytest.mark.django_db
class TestDocumentsAndImages:
    def test_document_tag_junction(self):
        doc = DocumentsFactory()
        tag = TagsFactory()
        DocumentTags.objects.create(DocumentId=doc, TagId=tag)
        assert doc.document_tags.count() == 1
        assert tag.tagged_documents.count() == 1

    def test_document_tag_cascades_on_document_delete(self):
        doc = DocumentsFactory()
        tag = TagsFactory()
        DocumentTags.objects.create(DocumentId=doc, TagId=tag)
        doc.delete()
        assert DocumentTags.objects.count() == 0

    def test_image_cover_defaults_false(self):
        assert ImagesFactory().IsCover is False

    def test_image_tag_junction(self):
        img = ImagesFactory()
        tag = TagsFactory()
        ImageTags.objects.create(ImageId=img, TagId=tag)
        assert img.image_tags.count() == 1
        assert tag.tagged_images.count() == 1


@pytest.mark.django_db
class TestEntityApiKeys:
    def test_create_defaults(self):
        key = EntityApiKeysFactory(KeyPrefix="sk_test")
        assert key.pk is not None
        assert key.Status == 1
        assert key.TargetEntityId is None
