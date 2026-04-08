from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="reportingperiod",
            constraint=models.UniqueConstraint(fields=("year", "week"), name="reports_unique_year_week"),
        ),
        migrations.AddConstraint(
            model_name="reportingperiod",
            constraint=models.UniqueConstraint(
                condition=Q(is_active=True),
                fields=("is_active",),
                name="reports_single_active_period",
            ),
        ),
    ]
