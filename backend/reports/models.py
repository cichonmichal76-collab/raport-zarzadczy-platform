from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta


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


class ProdioOrder(models.Model):
    prodio_id = models.CharField(max_length=128, unique=True)
    order_number = models.CharField(max_length=128, blank=True, db_index=True)
    status = models.CharField(max_length=64, blank=True, db_index=True)
    product_name = models.CharField(max_length=255, blank=True)
    product_group = models.CharField(max_length=255, blank=True)
    client_name = models.CharField(max_length=255, blank=True)
    total = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    done = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    deadline = models.DateField(null=True, blank=True)
    create_date = models.DateField(null=True, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)
    synced_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-create_date", "-id"]

    def __str__(self):
        return self.order_number or f"Prodio #{self.prodio_id}"


class ProdioApiObject(models.Model):
    resource = models.CharField(max_length=64, db_index=True)
    prodio_id = models.CharField(max_length=128)
    display_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=128, blank=True, db_index=True)
    raw_data = models.JSONField(default=dict, blank=True)
    synced_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["resource", "display_name", "prodio_id"]
        constraints = [
            models.UniqueConstraint(fields=["resource", "prodio_id"], name="reports_unique_prodio_api_object"),
        ]

    def __str__(self):
        return f"{self.resource}: {self.display_name or self.prodio_id}"


class ProdioSyncSettings(models.Model):
    STALE_RUNNING_MINUTES = 5

    INTERVAL_1 = 1
    INTERVAL_10 = 10
    INTERVAL_60 = 60
    INTERVAL_CHOICES = (
        (INTERVAL_1, "1 minuta"),
        (INTERVAL_10, "10 minut"),
        (INTERVAL_60, "1 godzina"),
    )

    enabled = models.BooleanField(default=True)
    interval_minutes = models.PositiveIntegerField(choices=INTERVAL_CHOICES, default=INTERVAL_10)
    last_started_at = models.DateTimeField(null=True, blank=True)
    last_finished_at = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=16, blank=True, default="never")
    last_message = models.TextField(blank=True)
    force_run_requested_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ustawienia sync Prodio"
        verbose_name_plural = "Ustawienia sync Prodio"

    def __str__(self):
        return "Sync Prodio"

    @classmethod
    def get_solo(cls):
        return cls.objects.get_or_create(pk=1)[0]

    def is_running(self):
        return bool(self.last_started_at and (not self.last_finished_at or self.last_started_at > self.last_finished_at))

    def is_stale_running(self, now=None):
        now = now or timezone.now()
        if not self.is_running() or not self.last_started_at:
            return False
        return now - self.last_started_at >= timedelta(minutes=self.STALE_RUNNING_MINUTES)

    def recover_stale_running(self, now=None):
        now = now or timezone.now()
        if not self.is_stale_running(now=now):
            return False
        self.last_finished_at = now
        self.last_status = "error"
        self.last_message = "stale running state recovered automatically"
        self.save(update_fields=["last_finished_at", "last_status", "last_message", "updated_at"])
        return True

    def is_due(self, now=None):
        now = now or timezone.now()
        if not self.enabled or self.is_running():
            return False
        if not self.last_finished_at:
            return True
        delta_minutes = (now - self.last_finished_at).total_seconds() / 60.0
        return delta_minutes >= self.interval_minutes

    def has_forced_run_pending(self):
        if not self.force_run_requested_at:
            return False
        if self.is_running():
            return False
        if not self.last_finished_at:
            return True
        if self.force_run_requested_at > self.last_finished_at:
            return True
        return self.last_status == "error" and bool(self.last_started_at and self.force_run_requested_at <= self.last_started_at)
