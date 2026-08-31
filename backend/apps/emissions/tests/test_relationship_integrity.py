"""Write-path tenant isolation and offset assurance regression tests."""

from datetime import date
from decimal import Decimal

from rest_framework import status

import pytest

from apps.emissions.models import EmissionsData, EmissionsOffsets, GHGInventories
from apps.entities.tests.factories import EntitiesFactory
from apps.projects.models import DevelopmentProjects, ProjectPhases

pytestmark = pytest.mark.django_db


def _emission_payload(gwp_dataset, **overrides):
    payload = {
        "Title": "Diesel use",
        "Scope": 1,
        "QuantityOrCost": "100.0000",
        "Unit": "litres",
        "EmissionFactor": "2.63900000",
        "EmissionFactorSource": "DEFRA test fixture",
        "Gas": "CO2",
        "GwpDatasetId": gwp_dataset.GwpDatasetId,
    }
    payload.update(overrides)
    return payload


def _create_emission(entity, gwp_dataset, title="Emission"):
    return EmissionsData.objects.create(
        EntityId=entity,
        Title=title,
        Scope=1,
        QuantityOrCost=Decimal("100.0000"),
        Unit="litres",
        EmissionFactor=Decimal("2.63900000"),
        EmissionFactorSource="DEFRA test fixture",
        Gas="CO2",
        GwpDatasetId=gwp_dataset,
    )


def _offset_payload(emission, **overrides):
    payload = {
        "EmissionsId": emission.EmissionsId,
        "Title": "Retired VCU",
        "OffsetType": "vcs",
        "Provider": "Verra",
        "OffsetAmountTonnes": "1.000000",
        "CreditRegistry": "verra",
        "CreditSerialNumber": "VCS-TEST-001",
    }
    payload.update(overrides)
    return payload


class TestEmissionRelationshipOwnership:
    def test_foreign_project_phase_and_inventory_are_rejected(
        self, auth_client, entity, gwp_dataset
    ):
        other = EntitiesFactory(EntityName="Other tenant")
        project = DevelopmentProjects.objects.create(EntityId=other, ProjectName="Other project")
        phase = ProjectPhases.objects.create(
            EntityId=other, ProjectId=project, PhaseName="Other phase"
        )
        inventory = GHGInventories.objects.create(
            EntityId=other,
            ReportingYear=2025,
            ReportingPeriodFrom=date(2025, 1, 1),
            ReportingPeriodTo=date(2025, 12, 31),
            GwpDatasetId=gwp_dataset,
        )

        response = auth_client.post(
            "/api/emissions/",
            _emission_payload(
                gwp_dataset,
                ProjectId=project.ProjectId,
                PhaseId=phase.PhaseId,
                InventoryId=inventory.InventoryId,
                ReportingYear=2025,
                ReportingPeriodFrom="2025-01-01",
                ReportingPeriodTo="2025-12-31",
            ),
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert {"ProjectId", "PhaseId", "InventoryId"}.issubset(response.data["errors"])
        assert not EmissionsData.objects.filter(EntityId=entity).exists()

    def test_same_entity_relationships_round_trip(self, auth_client, entity, gwp_dataset):
        project = DevelopmentProjects.objects.create(EntityId=entity, ProjectName="Own project")
        phase = ProjectPhases.objects.create(
            EntityId=entity, ProjectId=project, PhaseName="Own phase"
        )
        inventory = GHGInventories.objects.create(
            EntityId=entity,
            ReportingYear=2025,
            ReportingPeriodFrom=date(2025, 1, 1),
            ReportingPeriodTo=date(2025, 12, 31),
            GwpDatasetId=gwp_dataset,
        )

        response = auth_client.post(
            "/api/emissions/",
            _emission_payload(
                gwp_dataset,
                ProjectId=project.ProjectId,
                PhaseId=phase.PhaseId,
                InventoryId=inventory.InventoryId,
                ReportingYear=2025,
                ReportingPeriodFrom="2025-01-01",
                ReportingPeriodTo="2025-12-31",
            ),
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["ProjectId"] == project.ProjectId
        assert response.data["PhaseId"] == phase.PhaseId
        assert response.data["InventoryId"] == inventory.InventoryId
        assert response.data["GwpDatasetId"] == inventory.GwpDatasetId_id

    def test_phase_must_belong_to_selected_project(
        self, auth_client, entity, gwp_dataset
    ):
        first = DevelopmentProjects.objects.create(EntityId=entity, ProjectName="First")
        second = DevelopmentProjects.objects.create(EntityId=entity, ProjectName="Second")
        phase = ProjectPhases.objects.create(
            EntityId=entity, ProjectId=second, PhaseName="Second phase"
        )

        response = auth_client.post(
            "/api/emissions/",
            _emission_payload(
                gwp_dataset,
                ProjectId=first.ProjectId,
                PhaseId=phase.PhaseId,
            ),
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "PhaseId" in response.data["errors"]

    @pytest.mark.parametrize(
        "overrides,error_field",
        [
            (
                {
                    "ReportingYear": 2024,
                    "ReportingPeriodFrom": "2024-01-01",
                    "ReportingPeriodTo": "2024-12-31",
                },
                "ReportingYear",
            ),
            (
                {
                    "ReportingYear": 2025,
                    "ReportingPeriodFrom": "2024-12-31",
                    "ReportingPeriodTo": "2025-12-31",
                },
                "InventoryId",
            ),
        ],
    )
    def test_inventory_membership_requires_matching_year_and_boundary(
        self, overrides, error_field, auth_client, entity, gwp_dataset
    ):
        inventory = GHGInventories.objects.create(
            EntityId=entity,
            ReportingYear=2025,
            ReportingPeriodFrom=date(2025, 1, 1),
            ReportingPeriodTo=date(2025, 12, 31),
            GwpDatasetId=gwp_dataset,
        )

        response = auth_client.post(
            "/api/emissions/",
            _emission_payload(
                gwp_dataset,
                InventoryId=inventory.InventoryId,
                **overrides,
            ),
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error_field in response.data["errors"]

    def test_existing_emission_cannot_be_repointed_to_foreign_relationships(
        self, auth_client, entity, gwp_dataset
    ):
        created = auth_client.post(
            "/api/emissions/", _emission_payload(gwp_dataset), format="json"
        )
        assert created.status_code == status.HTTP_201_CREATED, created.data

        other = EntitiesFactory(EntityName="Other update tenant")
        project = DevelopmentProjects.objects.create(EntityId=other, ProjectName="Other project")
        phase = ProjectPhases.objects.create(
            EntityId=other, ProjectId=project, PhaseName="Other phase"
        )
        inventory = GHGInventories.objects.create(
            EntityId=other,
            ReportingYear=2025,
            ReportingPeriodFrom=date(2025, 1, 1),
            ReportingPeriodTo=date(2025, 12, 31),
            GwpDatasetId=gwp_dataset,
        )

        response = auth_client.patch(
            f"/api/emissions/{created.data['EmissionsId']}/",
            {
                "ProjectId": project.ProjectId,
                "PhaseId": phase.PhaseId,
                "InventoryId": inventory.InventoryId,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert {"ProjectId", "PhaseId", "InventoryId"}.issubset(response.data["errors"])
        emission = EmissionsData.objects.get(EmissionsId=created.data["EmissionsId"])
        assert emission.ProjectId is None
        assert emission.PhaseId is None
        assert emission.InventoryId is None


class TestStandaloneOffsetIntegrity:
    @pytest.fixture(autouse=True)
    def _enable_offsets(self, enable_feature, entity):
        enable_feature(entity, "carbon_offsets")

    def test_parent_is_required(self, auth_client):
        response = auth_client.post(
            "/api/emissions-offsets/",
            {
                "Title": "No parent",
                "OffsetType": "vcs",
                "Provider": "Verra",
                "OffsetAmountTonnes": "1.000000",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "EmissionsId" in response.data["errors"]

    def test_foreign_parent_is_rejected(self, auth_client, gwp_dataset):
        other = EntitiesFactory(EntityName="Other offset tenant")
        foreign_emission = _create_emission(other, gwp_dataset, "Foreign emission")

        response = auth_client.post(
            "/api/emissions-offsets/", _offset_payload(foreign_emission), format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "EmissionsId" in response.data["errors"]
        assert not EmissionsOffsets.objects.filter(EmissionsId=foreign_emission).exists()

    def test_same_entity_parent_is_persisted(
        self, auth_client, entity, gwp_dataset
    ):
        emission = _create_emission(entity, gwp_dataset)

        response = auth_client.post(
            "/api/emissions-offsets/", _offset_payload(emission), format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED, response.data
        offset = EmissionsOffsets.objects.get(OffsetId=response.data["OffsetId"])
        assert offset.EmissionsId == emission
        assert offset.EntityId == entity
        assert offset.RegistryValidationStatus == "unverified"

    def test_locked_parent_rejects_new_offset(
        self, auth_client, entity, gwp_dataset
    ):
        emission = _create_emission(entity, gwp_dataset)
        emission.VerificationStatus = 3
        emission.save(update_fields=["VerificationStatus"])

        response = auth_client.post(
            "/api/emissions-offsets/", _offset_payload(emission), format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not EmissionsOffsets.objects.filter(EmissionsId=emission).exists()

    @pytest.mark.parametrize(
        "field,value",
        [
            ("RegistryValidationStatus", "valid"),
            ("RegistryValidatedAt", "2026-08-25T12:00:00Z"),
            ("RegistryProjectName", "Forged project"),
            ("RegistryVintageYear", 2024),
        ],
    )
    def test_registry_results_cannot_be_forged_on_create(
        self, field, value, auth_client, entity, gwp_dataset
    ):
        emission = _create_emission(entity, gwp_dataset)

        response = auth_client.post(
            "/api/emissions-offsets/",
            _offset_payload(emission, **{field: value}),
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field in response.data["errors"]
        assert not EmissionsOffsets.objects.filter(EmissionsId=emission).exists()

    def test_identity_change_resets_registry_evidence(
        self, auth_client, entity, gwp_dataset
    ):
        emission = _create_emission(entity, gwp_dataset)
        offset = EmissionsOffsets.objects.create(
            EntityId=entity,
            EmissionsId=emission,
            Title="Validated credit",
            OffsetType="vcs",
            Provider="Verra",
            OffsetAmountTonnes="1.000000",
            CreditRegistry="verra",
            CreditSerialNumber="VCS-OLD",
            RegistryValidationStatus="valid",
            RegistryProjectName="Old verified project",
            RegistryVintageYear=2023,
        )

        response = auth_client.patch(
            f"/api/emissions-offsets/{offset.OffsetId}/",
            {"CreditSerialNumber": "VCS-NEW"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        offset.refresh_from_db()
        assert offset.RegistryValidationStatus == "unverified"
        assert offset.RegistryProjectName == ""
        assert offset.RegistryVintageYear is None

    def test_offset_cannot_be_reparented(
        self, auth_client, entity, gwp_dataset
    ):
        first = _create_emission(entity, gwp_dataset, "First emission")
        second = _create_emission(entity, gwp_dataset, "Second emission")
        created = auth_client.post(
            "/api/emissions-offsets/", _offset_payload(first), format="json"
        )
        assert created.status_code == status.HTTP_201_CREATED, created.data

        response = auth_client.patch(
            f"/api/emissions-offsets/{created.data['OffsetId']}/",
            {"EmissionsId": second.EmissionsId},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "EmissionsId" in response.data["errors"]
        offset = EmissionsOffsets.objects.get(OffsetId=created.data["OffsetId"])
        assert offset.EmissionsId == first

    def test_nested_offset_route_also_rejects_forged_registry_status(
        self, auth_client, entity, gwp_dataset
    ):
        emission = _create_emission(entity, gwp_dataset)

        response = auth_client.post(
            f"/api/emissions/{emission.EmissionsId}/offsets/",
            {
                "Title": "Forged nested credit",
                "OffsetType": "vcs",
                "Provider": "Verra",
                "OffsetAmountTonnes": "1.000000",
                "RegistryValidationStatus": "valid",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "RegistryValidationStatus" in response.data["errors"]
        assert not EmissionsOffsets.objects.filter(EmissionsId=emission).exists()
