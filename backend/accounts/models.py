from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Department(models.TextChoices):
        MANAGEMENT = "management", "Zarzad"
        PRODUCTION = "production", "Produkcja"
        RND = "rnd", "B+R"

    class Role(models.TextChoices):
        ADMIN = "admin", "Administrator"
        MANAGEMENT = "management", "Zarzad"
        PROD_EDITOR = "prod_editor", "Kierownik produkcji"
        RND_EDITOR = "rnd_editor", "Kierownik B+R"

    class StartDashboard(models.TextChoices):
        ZARZAD = "zarzad", "Raport Zarzad"
        PRODUKCJA = "produkcja", "Raport Produkcja"
        PRODIO = "prodio", "Raport Prodio"
        PRODIO_OPS = "prodio_ops", "Raport Operacje Prodio"
        BR = "br", "Raport B+R"

    role = models.CharField(max_length=32, choices=Role.choices, default=Role.MANAGEMENT)
    department = models.CharField(max_length=32, choices=Department.choices, default=Department.MANAGEMENT)
    start_dashboard = models.CharField(max_length=32, choices=StartDashboard.choices, blank=True, default="")
    display_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.display_name or self.username

    def save(self, *args, **kwargs):
        if self.role == self.Role.ADMIN:
            self.is_staff = True
        return super().save(*args, **kwargs)

    @property
    def effective_department(self):
        if self.department:
            return self.department
        if self.role == self.Role.PROD_EDITOR:
            return self.Department.PRODUCTION
        if self.role == self.Role.RND_EDITOR:
            return self.Department.RND
        return self.Department.MANAGEMENT

    @property
    def is_program_admin(self):
        return self.is_superuser or self.role == self.Role.ADMIN

    @property
    def default_start_dashboard(self):
        if self.effective_department == self.Department.PRODUCTION:
            return self.StartDashboard.PRODUKCJA
        if self.effective_department == self.Department.RND:
            return self.StartDashboard.BR
        return self.StartDashboard.ZARZAD
