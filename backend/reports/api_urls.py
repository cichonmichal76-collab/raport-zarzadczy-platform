from django.urls import path
from .api_views import DashboardSummaryApiView, ProductionRecordListApiView, RnDRecordListApiView

urlpatterns = [
    path("dashboard/", DashboardSummaryApiView.as_view(), name="api-dashboard-summary"),
    path("production/", ProductionRecordListApiView.as_view(), name="api-production-list"),
    path("rnd/", RnDRecordListApiView.as_view(), name="api-rnd-list"),
]
