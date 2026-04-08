from django.db import models
from reports.models import ReportingPeriod
import secrets


class PublishedReport(models.Model):
    period = models.ForeignKey(ReportingPeriod, on_delete=models.CASCADE, related_name="published_versions")
    token = models.CharField(max_length=64, unique=True, default=secrets.token_hex)
    title = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
