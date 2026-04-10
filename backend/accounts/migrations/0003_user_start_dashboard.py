from django.db import migrations, models


def set_start_dashboard_defaults(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for user in User.objects.all():
        if user.department == "production":
            user.start_dashboard = "produkcja"
        elif user.department == "rnd":
            user.start_dashboard = "br"
        else:
            user.start_dashboard = "zarzad"
        user.save(update_fields=["start_dashboard"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_user_department"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="start_dashboard",
            field=models.CharField(
                blank=True,
                choices=[
                    ("zarzad", "Raport Zarzad"),
                    ("produkcja", "Raport Produkcja"),
                    ("prodio", "Raport Prodio"),
                    ("prodio_ops", "Raport Operacje Prodio"),
                    ("br", "Raport B+R"),
                ],
                default="",
                max_length=32,
            ),
        ),
        migrations.RunPython(set_start_dashboard_defaults, migrations.RunPython.noop),
    ]
