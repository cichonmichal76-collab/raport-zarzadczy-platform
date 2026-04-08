from django.contrib import admin
from .models import ProductionRecord, ReportingPeriod, RnDRecord


@admin.register(ReportingPeriod)
class ReportingPeriodAdmin(admin.ModelAdmin):
    list_display = ("name", "year", "week", "is_active", "is_published")
    list_filter = ("year", "is_active", "is_published")


@admin.register(ProductionRecord)
class ProductionRecordAdmin(admin.ModelAdmin):
    list_display = ("order_number", "status", "product", "period")
    list_filter = ("status", "period")
    search_fields = ("order_number", "product")


@admin.register(RnDRecord)
class RnDRecordAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "progress", "trl_level", "period")
    list_filter = ("status", "period")
    search_fields = ("code", "name")
