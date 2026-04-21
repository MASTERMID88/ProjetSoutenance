from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)

    # Ajout du champ `role` dans la fiche d'edition
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Role metier", {"fields": ("role",)}),
    )

    # Ajout du champ `role` dans le formulaire de CREATION
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2", "role",
                       "first_name", "last_name", "email"),
        }),
    )
