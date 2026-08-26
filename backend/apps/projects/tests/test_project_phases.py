"""Project-phase workflow and integrity tests."""

from datetime import date
from decimal import Decimal

from rest_framework import status

import pytest

from apps.emissions.models import EmissionsData
from apps.entities.tests.factories import EntitiesFactory
from apps.projects.models import DevelopmentProjects, ProjectPhases

pytestmark = pytest.mark.django_db


def _project(entity, name="Retrofit programme"):
    return DevelopmentProjects.objects.create(EntityId=entity, ProjectName=name)


class TestProjectPhaseWorkflow:
    def test_create_edit_and_list_phase(self, auth_client, entity):
        project = _project(entity)
        created = auth_client.post(
            f"/api/projects/{project.ProjectId}/phases/",
            {
                "PhaseName": "Design",
                "PhaseNumber": 1,
                "StartDate": "2025-01-01",
                "EndDate": "2025-03-31",
                "TargetEmissionsTonnes": "12.5000",
            },
            format="json",
        )

        assert created.status_code == status.HTTP_201_CREATED, created.data
        phase_id = created.data["PhaseId"]
        phase = ProjectPhases.objects.get(PhaseId=phase_id)
        assert phase.EntityId == entity
        assert phase.ProjectId == project

        updated = auth_client.patch(
            f"/api/projects/{project.ProjectId}/phases/{phase_id}/",
            {"PhaseName": "Detailed design"},
            format="json",
        )
        assert updated.status_code == status.HTTP_200_OK, updated.data

        listed = auth_client.get(f"/api/projects/{project.ProjectId}/phases/")
        assert listed.status_code == status.HTTP_200_OK
        assert listed.data[0]["PhaseName"] == "Detailed design"

    def test_invalid_phase_dates_are_rejected(self, auth_client, entity):
        project = _project(entity)

        response = auth_client.post(
            f"/api/projects/{project.ProjectId}/phases/",
            {
                "PhaseName": "Impossible phase",
                "StartDate": "2025-04-01",
                "EndDate": "2025-03-31",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "EndDate" in response.data["errors"]

    def test_other_tenant_project_is_not_visible(self, auth_client):
        other = EntitiesFactory(EntityName="Other project tenant")
        project = _project(other)

        response = auth_client.get(f"/api/projects/{project.ProjectId}/phases/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_phase_assigned_to_emissions_cannot_be_removed(
        self, auth_client, entity, gwp_dataset
    ):
        project = _project(entity)
        phase = ProjectPhases.objects.create(
            EntityId=entity,
            ProjectId=project,
            PhaseName="Construction",
        )
        EmissionsData.objects.create(
            EntityId=entity,
            ProjectId=project,
            PhaseId=phase,
            Title="Site diesel",
            Scope=1,
            QuantityOrCost=Decimal("10.0000"),
            Unit="litres",
            EmissionFactor=Decimal("2.63900000"),
            EmissionFactorSource="Test factor",
            Gas="CO2",
            GwpDatasetId=gwp_dataset,
            ReportingYear=2025,
            ReportingPeriodFrom=date(2025, 1, 1),
            ReportingPeriodTo=date(2025, 1, 31),
        )

        response = auth_client.delete(
            f"/api/projects/{project.ProjectId}/phases/{phase.PhaseId}/"
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data["code"] == "phase_in_use"
        phase.refresh_from_db()
        assert phase.Status < 4
