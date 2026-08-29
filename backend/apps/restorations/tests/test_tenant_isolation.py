"""Tenant-owned relationship validation for nature MRV writes."""

from rest_framework import status

import pytest

from apps.ecosystem.models import Species
from apps.entities.tests.factories import EntitiesFactory
from apps.projects.models import DevelopmentProjects
from apps.restorations.models import (
    Restorations,
    RestorationSpecies,
    TreeRemovalAffectedSpecies,
    TreeRemovalRemovedSpecies,
    TreeRemovals,
)

pytestmark = pytest.mark.django_db


def test_tree_removal_project_must_belong_to_active_entity(auth_client, entity):
    other = EntitiesFactory(EntityName="Other nature tenant")
    foreign_project = DevelopmentProjects.objects.create(
        EntityId=other, ProjectName="Foreign project"
    )

    rejected = auth_client.post(
        "/api/tree-removals/",
        {"Description": "Removal", "ProjectId": foreign_project.ProjectId},
        format="json",
    )
    assert rejected.status_code == status.HTTP_400_BAD_REQUEST
    assert "ProjectId" in rejected.data["errors"]
    assert not TreeRemovals.objects.filter(EntityId=entity).exists()

    own_project = DevelopmentProjects.objects.create(EntityId=entity, ProjectName="Own project")
    accepted = auth_client.post(
        "/api/tree-removals/",
        {"Description": "Removal", "ProjectId": own_project.ProjectId},
        format="json",
    )
    assert accepted.status_code == status.HTTP_201_CREATED, accepted.data
    assert accepted.data["ProjectId"] == own_project.ProjectId

    removal_id = accepted.data["TreeRemovalId"]
    repoint = auth_client.patch(
        f"/api/tree-removals/{removal_id}/",
        {"ProjectId": foreign_project.ProjectId},
        format="json",
    )
    assert repoint.status_code == status.HTTP_400_BAD_REQUEST
    assert "ProjectId" in repoint.data["errors"]
    assert TreeRemovals.objects.get(TreeRemovalId=removal_id).ProjectId == own_project


def test_removed_species_must_belong_to_removal_entity(auth_client, entity):
    other = EntitiesFactory(EntityName="Other species tenant")
    foreign_species = Species.objects.create(EntityId=other, CommonName="Foreign tree")
    own_species = Species.objects.create(EntityId=entity, CommonName="Own tree")
    removal = TreeRemovals.objects.create(EntityId=entity, Description="Removal")
    url = f"/api/tree-removals/{removal.TreeRemovalId}/removed-species/"

    rejected = auth_client.post(url, {"SpeciesId": foreign_species.SpeciesId}, format="json")
    assert rejected.status_code == status.HTTP_400_BAD_REQUEST
    assert "SpeciesId" in rejected.data["errors"]
    assert not removal.removed_species.exists()

    accepted = auth_client.post(
        url, {"SpeciesId": own_species.SpeciesId, "Count": 1}, format="json"
    )
    assert accepted.status_code == status.HTTP_201_CREATED, accepted.data
    assert accepted.data["SpeciesId"] == own_species.SpeciesId


def test_affected_species_must_belong_to_removal_entity(auth_client, entity):
    other = EntitiesFactory(EntityName="Other affected tenant")
    foreign_species = Species.objects.create(EntityId=other, CommonName="Foreign habitat")
    removal = TreeRemovals.objects.create(EntityId=entity, Description="Removal")

    response = auth_client.post(
        f"/api/tree-removals/{removal.TreeRemovalId}/affected-species/",
        {"SpeciesId": foreign_species.SpeciesId, "Notes": "Should fail"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "SpeciesId" in response.data["errors"]
    assert not removal.affected_species.exists()


def test_restoration_species_must_belong_to_restoration_entity(auth_client, entity):
    other = EntitiesFactory(EntityName="Other restoration tenant")
    foreign_species = Species.objects.create(EntityId=other, CommonName="Foreign planting")
    restoration = Restorations.objects.create(
        EntityId=entity, RestorationName="Own restoration"
    )

    response = auth_client.post(
        f"/api/restorations/{restoration.RestorationId}/species/",
        {"SpeciesId": foreign_species.SpeciesId, "Count": 10},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "SpeciesId" in response.data["errors"]
    assert not restoration.restoration_species.exists()


def test_nature_child_rows_cannot_be_repointed_to_foreign_species(auth_client, entity):
    other = EntitiesFactory(EntityName="Other child update tenant")
    foreign_species = Species.objects.create(EntityId=other, CommonName="Foreign species")
    own_species = Species.objects.create(EntityId=entity, CommonName="Own species")
    removal = TreeRemovals.objects.create(EntityId=entity, Description="Removal")
    restoration = Restorations.objects.create(
        EntityId=entity, RestorationName="Own restoration"
    )
    removed = TreeRemovalRemovedSpecies.objects.create(
        TreeRemovalId=removal, SpeciesId=own_species, Count=1
    )
    affected = TreeRemovalAffectedSpecies.objects.create(
        TreeRemovalId=removal, SpeciesId=own_species
    )
    planted = RestorationSpecies.objects.create(
        RestorationId=restoration, SpeciesId=own_species, Count=1
    )

    attempts = (
        (
            f"/api/tree-removals/{removal.TreeRemovalId}/removed-species/{removed.id}/",
            removed,
        ),
        (
            f"/api/tree-removals/{removal.TreeRemovalId}/affected-species/{affected.id}/",
            affected,
        ),
        (
            f"/api/restorations/{restoration.RestorationId}/species/{planted.id}/",
            planted,
        ),
    )

    for url, instance in attempts:
        response = auth_client.patch(
            url, {"SpeciesId": foreign_species.SpeciesId}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "SpeciesId" in response.data["errors"]
        instance.refresh_from_db()
        assert instance.SpeciesId == own_species
