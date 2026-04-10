from django.urls import path

from .views import (
    BiReportsView,
    DashboardView,
    FullGrafanaView,
    LoginSyncStatusView,
    LoginSyncWaitView,
    ProdioSyncControlView,
    ProductionView,
    RnDView,
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("grafana-full/", FullGrafanaView.as_view(), name="full-grafana"),
    path("production/", ProductionView.as_view(), name="production-list"),
    path("rnd/", RnDView.as_view(), name="rnd-list"),
    path("bi/", BiReportsView.as_view(), name="bi-reports"),
    path("prodio-sync-control/", ProdioSyncControlView.as_view(), name="prodio-sync-control"),
    path("login-sync-wait/", LoginSyncWaitView.as_view(), name="login-sync-wait"),
    path("login-sync-status/", LoginSyncStatusView.as_view(), name="login-sync-status"),
]
