from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ReportingPeriod",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("year", models.PositiveIntegerField()),
                ("week", models.PositiveIntegerField()),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("is_active", models.BooleanField(default=False)),
                ("is_published", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-year", "-week"]},
        ),
        migrations.CreateModel(
            name="ProductionRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_number", models.CharField(max_length=128)),
                ("status", models.CharField(max_length=64)),
                ("product", models.CharField(max_length=255)),
                ("product_group", models.CharField(blank=True, max_length=128)),
                ("machine", models.CharField(blank=True, max_length=128)),
                ("completed_units", models.PositiveIntegerField(default=0)),
                ("planned_units", models.PositiveIntegerField(default=0)),
                ("work_time", models.CharField(blank=True, max_length=32)),
                ("norm_time", models.CharField(blank=True, max_length=32)),
                ("workers", models.CharField(blank=True, max_length=512)),
                ("current_state", models.TextField(blank=True)),
                ("problem", models.TextField(blank=True)),
                ("solution", models.TextField(blank=True)),
                ("period", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="production_records", to="reports.reportingperiod")),
            ],
        ),
        migrations.CreateModel(
            name="RnDRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64)),
                ("name", models.CharField(max_length=255)),
                ("status", models.CharField(max_length=64)),
                ("progress", models.PositiveIntegerField(default=0)),
                ("trl_level", models.PositiveIntegerField(default=5)),
                ("milestone", models.CharField(blank=True, max_length=255)),
                ("work_type", models.CharField(blank=True, max_length=255)),
                ("parameters", models.TextField(blank=True)),
                ("current_state", models.TextField(blank=True)),
                ("problem", models.TextField(blank=True)),
                ("solution", models.TextField(blank=True)),
                ("period", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="rnd_records", to="reports.reportingperiod")),
            ],
        ),
    ]
