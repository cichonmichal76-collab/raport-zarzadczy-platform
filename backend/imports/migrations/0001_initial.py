from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UploadBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(choices=[("production", "Produkcja"), ("rnd", "B+R")], max_length=32)),
                ("status", models.CharField(choices=[("pending", "Oczekuje"), ("processing", "W trakcie"), ("success", "Sukces"), ("failed", "Błąd")], default="pending", max_length=32)),
                ("file", models.FileField(upload_to="uploads/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("period", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="upload_batches", to="reports.reportingperiod")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="ImportLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("level", models.CharField(default="info", max_length=16)),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="logs", to="imports.uploadbatch")),
            ],
            options={"ordering": ["created_at"]},
        ),
    ]
