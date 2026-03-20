from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Group,
    Permission,
    PermissionsMixin,
)
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, name, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number is required")
        user = self.model(phone_number=phone_number, name=name, **extra_fields)
        if password:
            user.set_password(password)  # для админа
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, name=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)

        return self.create_user(phone_number, name, password, **extra_fields)


class UserRole(models.TextChoices):
    USER = "user", "User"
    ADMIN = "admin", "Admin"


class UserModels(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150, null=True, blank=True)
    role = models.CharField(
        max_length=10, choices=[("user", "User"), ("admin", "Admin")], default="user"
    )

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    access_token = models.CharField(max_length=255, blank=True, null=True)
    access_expiration = models.DateTimeField(blank=True, null=True)
    refresh_token = models.CharField(max_length=255, blank=True, null=True)
    refresh_expiration = models.DateTimeField(blank=True, null=True)

    otp_code = models.PositiveIntegerField(blank=True, null=True)
    otp_expiration = models.DateTimeField(blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    # Исправляем related_name для ManyToMany полей PermissionsMixin
    groups = models.ManyToManyField(
        Group,
        verbose_name="groups",
        blank=True,
        help_text="The groups this user belongs to.",
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="custom_user_permissions_set",
        related_query_name="custom_user_permissions",
    )


class Level(models.TextChoices):
    SILVER = "Silver", "Silver"
    GOLD = "Gold", "Gold"
    BLACK = "Black", "Black"


class Employee(models.Model):
    user = models.OneToOneField(UserModels, on_delete=models.CASCADE, related_name="employee")
    name = models.CharField(max_length=255, verbose_name="ФИО сотрудника")
    position = models.CharField(max_length=100, verbose_name="Должность")

    deals_count = models.IntegerField(
        default=0, verbose_name="Количество сделок (факт)"
    )
    deals_plan = models.IntegerField(
        default=10, verbose_name="Количество сделок (план)"
    )
    volume = models.FloatField(default=0, verbose_name="Объём сделок, млн ₽ (факт)")
    volume_plan = models.FloatField(
        default=10, verbose_name="Объём сделок, млн ₽ (план)"
    )
    bank_share = models.FloatField(default=0, verbose_name="Доля банка, % (факт)")
    bank_share_goal = models.FloatField(
        default=50, verbose_name="Целевая доля банка, %"
    )
    approved_requests = models.IntegerField(default=0, verbose_name="Одобренные заявки")
    submitted_requests = models.IntegerField(default=0, verbose_name="Поданные заявки")

    level = models.CharField(
        max_length=20,
        choices=Level.choices,
        default=Level.SILVER,
        verbose_name="Уровень сотрудника",
    )
    points = models.FloatField(default=0, verbose_name="Баллы сотрудника")

    def __str__(self):
        return self.name
