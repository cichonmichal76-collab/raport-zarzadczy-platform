from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class ReportingPeriod(models.Model):
    name = models.CharField(max_length=255)
    year = models.PositiveIntegerField()
    week = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-year", "-week"]
        constraints = [
            models.UniqueConstraint(fields=["year", "week"], name="reports_unique_year_week"),
            models.UniqueConstraint(
                fields=["is_active"],
                condition=Q(is_active=True),
                name="reports_single_active_period",
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.is_active:
            existing = ReportingPeriod.objects.filter(is_active=True).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError({"is_active": "Tylko jeden okres raportowy może być aktywny."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ProductionRecord(models.Model):
    period = models.ForeignKey(ReportingPeriod, on_delete=models.CASCADE, related_name="production_records")
    order_number = models.CharField(max_length=128)
    status = models.CharField(max_length=64)
    product = models.CharField(max_length=255)
    product_group = models.CharField(max_length=128, blank=True)
    machine = models.CharField(max_length=128, blank=True)
    completed_units = models.PositiveIntegerField(default=0)
    planned_units = models.PositiveIntegerField(default=0)
    work_time = models.CharField(max_length=32, blank=True)
    norm_time = models.CharField(max_length=32, blank=True)
    workers = models.CharField(max_length=512, blank=True)
    current_state = models.TextField(blank=True)
    problem = models.TextField(blank=True)
    solution = models.TextField(blank=True)

    def __str__(self):
        return f"{self.order_number} - {self.product}"


class RnDRecord(models.Model):
    period = models.ForeignKey(ReportingPeriod, on_delete=models.CASCADE, related_name="rnd_records")
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=64)
    progress = models.PositiveIntegerField(default=0)
    trl_level = models.PositiveIntegerField(default=5)
    milestone = models.CharField(max_length=255, blank=True)
    work_type = models.CharField(max_length=255, blank=True)
    parameters = models.TextField(blank=True)
    current_state = models.TextField(blank=True)
    problem = models.TextField(blank=True)
    solution = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"
