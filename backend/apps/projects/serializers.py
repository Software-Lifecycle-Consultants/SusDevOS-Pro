from rest_framework import serializers
from .models import DevelopmentProjects, ProjectPhases, DevelopmentProjectPartners


class ProjectPhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhases
        fields = ("PhaseId", "PhaseName", "PhaseNumber", "Description",
                  "StartDate", "EndDate", "TargetEmissionsTonnes", "Status")
        read_only_fields = ("PhaseId",)


class DevelopmentProjectsListSerializer(serializers.ModelSerializer):
    phase_count = serializers.SerializerMethodField()

    class Meta:
        model = DevelopmentProjects
        fields = ("ProjectId", "ProjectName", "ProjectReference", "ProjectType",
                  "Country", "StartDate", "EndDate", "Status", "phase_count")

    def get_phase_count(self, obj):
        return obj.phases.filter(Status__lt=4).count()


class DevelopmentProjectsDetailSerializer(serializers.ModelSerializer):
    phases = ProjectPhaseSerializer(many=True, read_only=True)

    class Meta:
        model = DevelopmentProjects
        fields = "__all__"
        read_only_fields = ("ProjectId", "EntityId", "CreatedAt", "UpdatedAt", "CreatedBy", "UpdatedBy")


class ProjectPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DevelopmentProjectPartners
        fields = ("id", "EntityId", "PartnerSharePercent",
                  "PartnerConsolidationApproach", "IsDoubleCountingRisk", "DoubleCountingNotes")
