from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("imports", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="uploadbatch",
            name="records_imported",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="uploadbatch",
            name="rows_skipped",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
