from django.db import migrations, models


def set_department_from_role(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for user in User.objects.all():
        if user.role == "prod_editor":
            user.department = "production"
        elif user.role == "rnd_editor":
            user.department = "rnd"
        else:
            user.department = "management"
        user.save(update_fields=["department"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="department",
            field=models.CharField(
                choices=[("management", "Zarzad"), ("production", "Produkcja"), ("rnd", "B+R")],
                default="management",
                max_length=32,
            ),
        ),
        migrations.RunPython(set_department_from_role, migrations.RunPython.noop),
    ]
