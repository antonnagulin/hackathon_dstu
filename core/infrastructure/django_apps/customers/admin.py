from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Employee, UserModels


@admin.register(UserModels)
class CustomUserAdmin(UserAdmin):
    model = UserModels
    list_display = ("phone_number", "name", "is_verified", "is_staff", "is_superuser")
    list_filter = ("is_verified", "is_staff", "is_superuser")
    search_fields = ("phone_number", "name")
    ordering = ("phone_number",)
    fieldsets = (
        (None, {"fields": ("phone_number", "name", "password")}),
        (
            "Permissions",
            {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (
            "Tokens",
            {
                "fields": (
                    "access_token",
                    "access_expiration",
                    "refresh_token",
                    "refresh_expiration",
                )
            },
        ),
        ("OTP", {"fields": ("otp_code", "otp_expiration")}),
    )


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("name", "position", "level", "points")
