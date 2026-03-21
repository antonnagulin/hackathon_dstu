from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Employee, LevelBenefit, RatingConfig, UserModels


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




@admin.register(LevelBenefit)
class LevelBenefitAdmin(admin.ModelAdmin):
    list_display = (
        "level",
        "income_growth_year",
        "mortgage_saving_year",
        "other_benefit_year",
        "is_active",
        "updated_at",
    )
    list_filter = ("level", "is_active")
    search_fields = ("level", "title", "description")



@admin.register(RatingConfig)
class RatingConfigAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "gold_from",
        "black_from",
        "max_index",
        "weight_volume",
        "weight_deals",
        "weight_bank_share",
        "weight_conversion",
        "gold_bonus",
        "black_bonus",
        "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Общее",
            {
                "fields": (
                    "name",
                    "is_active",
                )
            },
        ),
        (
            "Пороги уровней",
            {
                "fields": (
                    "gold_from",
                    "black_from",
                    "max_index",
                )
            },
        ),
        (
            "Веса показателей",
            {
                "fields": (
                    "weight_volume",
                    "weight_deals",
                    "weight_bank_share",
                    "weight_conversion",
                )
            },
        ),
        (
            "Бонусы по уровням",
            {
                "fields": (
                    "silver_bonus",
                    "gold_bonus",
                    "black_bonus",
                )
            },
        ),
        (
            "Служебные поля",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
