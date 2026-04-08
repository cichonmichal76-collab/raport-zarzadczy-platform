from django.conf import settings
from django.db import models

from reports.models import ReportingPeriod


class UploadBatch(models.Model):
    class Source(models.TextChoices):
        PRODUCTION = "production", "Produkcja"
        RND = "rnd", "B+R"

    class Status(models.TextChoices):
        PENDING = "pending", "Oczekuje"
        PROCESSING = "processing", "W trakcie"
        SUCCESS = "success", "Sukces"
        FAILED = "failed", "Blad"

    period = models.ForeignKey(ReportingPeriod, on_delete=models.CASCADE, related_name="upload_batches")
    source = models.CharField(max_length=32, choices=Source.choices)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    file = models.FileField(upload_to="uploads/")
    records_imported = models.PositiveIntegerField(default=0)
    rows_skipped = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.period} / {self.source}"


class ImportLog(models.Model):
    batch = models.ForeignKey(UploadBatch, on_delete=models.CASCADE, related_name="logs")
    level = models.CharField(max_length=16, default="info")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
