from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView
from .models import PublishedReport


class PublishedReportDetailView(DetailView):
    template_name = "publishing/published_report.html"
    context_object_name = "published_report"

    def get_object(self):
        return get_object_or_404(PublishedReport, token=self.kwargs["token"], is_active=True)
