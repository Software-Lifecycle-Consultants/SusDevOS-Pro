from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ReportJobsViewSet

router = DefaultRouter()
router.register("", ReportJobsViewSet, basename="reports")
urlpatterns = [path("", include(router.urls))]
