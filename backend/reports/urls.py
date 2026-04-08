from django.urls import path
from .views import BiReportsView, DashboardView, ProductionView, RnDView

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("production/", ProductionView.as_view(), name="production-list"),
    path("rnd/", RnDView.as_view(), name="rnd-list"),
    path("bi/", BiReportsView.as_view(), name="bi-reports"),
]
