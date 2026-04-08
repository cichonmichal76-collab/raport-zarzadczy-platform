from django.contrib import admin
from .models import PublishedReport


@admin.register(PublishedReport)
class PublishedReportAdmin(admin.ModelAdmin):
    list_display = ("title", "period", "is_active", "created_at")
    list_filter = ("is_active", "period")
