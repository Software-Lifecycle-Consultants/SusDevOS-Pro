from rest_framework import serializers

from .models import DevelopmentProjectPartners, DevelopmentProjects, ProjectPhases


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
        # Prefer the queryset annotation (see DevelopmentProjectsViewSet.get_queryset)
        # to avoid an N+1 COUNT per row; fall back to a query if unannotated.
        annotated = getattr(obj, "active_phase_count", None)
        if annotated is not None:
            return annotated
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
