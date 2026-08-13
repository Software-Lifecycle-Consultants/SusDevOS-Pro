from django.contrib import admin

from .models import (
    DevelopmentProjectContacts,
    DevelopmentProjectDocuments,
    DevelopmentProjectEntities,
    DevelopmentProjectImages,
    DevelopmentProjectLandParcels,
    DevelopmentProjectPartners,
    DevelopmentProjects,
    DevelopmentProjectTags,
    ProjectPhases,
    RelatedProjects,
)


class ProjectPhasesInline(admin.TabularInline):
    model = ProjectPhases
    extra = 0
    fields = ("PhaseName", "PhaseNumber", "StartDate", "EndDate", "Status")

@admin.register(DevelopmentProjects)
class DevelopmentProjectsAdmin(admin.ModelAdmin):
    list_display = ("ProjectId", "ProjectName", "EntityId", "Country", "StartDate", "Status")
    list_filter = ("ProjectType", "Status", "Country")
    search_fields = ("ProjectName", "ProjectReference")
    raw_id_fields = ("EntityId",)
    inlines = [ProjectPhasesInline]

@admin.register(ProjectPhases)
class ProjectPhasesAdmin(admin.ModelAdmin):
    list_display = ("PhaseId", "PhaseName", "ProjectId", "PhaseNumber", "StartDate", "Status")
    raw_id_fields = ("ProjectId", "EntityId")

admin.site.register(RelatedProjects)
admin.site.register(DevelopmentProjectTags)
admin.site.register(DevelopmentProjectPartners)
admin.site.register(DevelopmentProjectLandParcels)
admin.site.register(DevelopmentProjectContacts)
admin.site.register(DevelopmentProjectDocuments)
admin.site.register(DevelopmentProjectImages)
admin.site.register(DevelopmentProjectEntities)
