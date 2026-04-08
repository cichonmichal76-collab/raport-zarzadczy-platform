from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrator"
        MANAGEMENT = "management", "Zarząd"
        PROD_EDITOR = "prod_editor", "Kierownik produkcji"
        RND_EDITOR = "rnd_editor", "Kierownik B+R"

    role = models.CharField(max_length=32, choices=Role.choices, default=Role.MANAGEMENT)
    display_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.display_name or self.username
