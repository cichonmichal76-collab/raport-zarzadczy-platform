from celery import shared_task
from django.db import transaction

from .models import ImportLog, UploadBatch
from .services import ImportValidationError, process_batch


@shared_task
def process_upload_batch(batch_id: int):
    batch = UploadBatch.objects.get(pk=batch_id)
    batch.status = UploadBatch.Status.PROCESSING
    batch.records_imported = 0
    batch.rows_skipped = 0
    batch.save(update_fields=["status", "records_imported", "rows_skipped"])

    ImportLog.objects.create(batch=batch, level="info", message="Rozpoczeto przetwarzanie wsadu.")

    try:
        with transaction.atomic():
            summary = process_batch(batch)
        batch.records_imported = summary.get("records_imported", 0)
        batch.rows_skipped = summary.get("rows_skipped", 0)
        batch.status = UploadBatch.Status.SUCCESS
        batch.save(update_fields=["status", "records_imported", "rows_skipped"])
        ImportLog.objects.create(batch=batch, level="info", message="Przetwarzanie zakonczone.")
    except ImportValidationError as exc:
        batch.status = UploadBatch.Status.FAILED
        batch.save(update_fields=["status"])
        ImportLog.objects.create(batch=batch, level="error", message=str(exc))
    except Exception as exc:
        batch.status = UploadBatch.Status.FAILED
        batch.save(update_fields=["status"])
        ImportLog.objects.create(batch=batch, level="error", message=f"Nieoczekiwany blad importu: {exc}")
