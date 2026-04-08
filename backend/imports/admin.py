from django.contrib import admin
from .models import ImportLog, UploadBatch


class ImportLogInline(admin.TabularInline):
    model = ImportLog
    extra = 0
    readonly_fields = ("level", "message", "created_at")


@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = ("period", "source", "status", "uploaded_by", "created_at")
    list_filter = ("source", "status", "period")
    inlines = [ImportLogInline]
