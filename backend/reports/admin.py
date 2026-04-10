from django.contrib import admin
from .models import ProdioApiObject, ProdioOrder, ProdioSyncSettings, ProductionRecord, ReportingPeriod, RnDRecord


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


@admin.register(ProdioOrder)
class ProdioOrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "status", "product_name", "client_name", "total", "done", "deadline", "synced_at")
    list_filter = ("status", "deadline", "synced_at")
    search_fields = ("prodio_id", "order_number", "product_name", "client_name")
    readonly_fields = ("prodio_id", "raw_data", "synced_at", "updated_at")


@admin.register(ProdioApiObject)
class ProdioApiObjectAdmin(admin.ModelAdmin):
    list_display = ("resource", "prodio_id", "display_name", "status", "synced_at")
    list_filter = ("resource", "status", "synced_at")
    search_fields = ("prodio_id", "display_name")
    readonly_fields = ("resource", "prodio_id", "raw_data", "synced_at", "updated_at")


@admin.register(ProdioSyncSettings)
class ProdioSyncSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "enabled", "interval_minutes", "last_status", "last_started_at", "last_finished_at", "updated_at")
    readonly_fields = ("last_started_at", "last_finished_at", "last_status", "last_message", "force_run_requested_at", "updated_at")

    def has_add_permission(self, request):
        if ProdioSyncSettings.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False
