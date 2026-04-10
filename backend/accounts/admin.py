from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Profil w programie", {"fields": ("display_name", "email", "role", "department")}),
        (
            "Dostep",
            {
                "fields": ("is_active", "is_staff", "is_superuser"),
                "description": (
                    "Rola steruje menu i widokami programu. "
                    "Dostep do panelu Django Admin wymaga zaznaczenia is_staff. "
                    "Superuser omija wszystkie ograniczenia."
                ),
            },
        ),
        ("Daty", {"fields": ("last_login", "date_joined"), "classes": ("collapse",)}),
        ("Zaawansowane Django", {"fields": ("groups", "user_permissions"), "classes": ("collapse",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Profil w programie", {"fields": ("display_name", "email", "role", "department")}),
    )
    list_display = ("username", "email", "role", "department", "is_active", "is_staff", "is_superuser")
    list_filter = ("role", "department", "is_active", "is_staff", "is_superuser")
