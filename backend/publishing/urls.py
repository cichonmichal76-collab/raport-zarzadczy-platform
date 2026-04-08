from django.urls import path
from .views import PublishedReportDetailView

urlpatterns = [
    path("<str:token>/", PublishedReportDetailView.as_view(), name="published-report"),
]
