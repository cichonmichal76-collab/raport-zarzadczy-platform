import secrets
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PublishedReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.CharField(default=secrets.token_hex, max_length=64, unique=True)),
                ("title", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("period", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="published_versions", to="reports.reportingperiod")),
            ],
        ),
    ]
