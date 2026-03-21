from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Group,
    Permission,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError
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
    email = models.CharField(max_length=100, verbose_name="Email", blank=True)

    dealer_code = models.CharField(max_length=100, verbose_name="dealer_code", blank=True)
    
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

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано"
    )
    def __str__(self):
        return self.name



class RatingConfig(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название конфигурации"
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name="Активна"
    )

    gold_from = models.FloatField(
        default=70.0,
        verbose_name="Порог уровня Gold (балл)"
    )
    black_from = models.FloatField(
        default=90.0,
        verbose_name="Порог уровня Black (балл)"
    )
    max_index = models.FloatField(
        default=120.0,
        verbose_name="Максимальный индекс рейтинга"
    )

    weight_volume = models.FloatField(
        default=0.35,
        verbose_name="Вес показателя объёма продаж"
    )
    weight_deals = models.FloatField(
        default=0.25,
        verbose_name="Вес показателя количества сделок"
    )
    weight_bank_share = models.FloatField(
        default=0.25,
        verbose_name="Вес показателя доли банка"
    )
    weight_conversion = models.FloatField(
        default=0.15,
        verbose_name="Вес показателя конверсии"
    )

    silver_bonus = models.FloatField(
        default=0.0,
        verbose_name="Бонус уровня Silver (руб.)"
    )
    gold_bonus = models.FloatField(
        default=20000.0,
        verbose_name="Бонус уровня Gold (руб.)"
    )
    black_bonus = models.FloatField(
        default=40000.0,
        verbose_name="Бонус уровня Black (руб.)"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлено"
    )

    class Meta:
        verbose_name = "Конфигурация рейтинга"
        verbose_name_plural = "Конфигурации рейтинга"

    def clean(self):
        weight_sum = (
            self.weight_volume
            + self.weight_deals
            + self.weight_bank_share
            + self.weight_conversion
        )
        if round(weight_sum, 6) != 1.0:
            raise ValidationError("Сумма весов должна быть равна 1.0")

        if self.gold_from >= self.black_from:
            raise ValidationError("Порог Gold должен быть меньше порога Black")

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.is_active:
            RatingConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class LevelBenefit(models.Model):
    level = models.CharField(
        max_length=20,
        choices=Level.choices,
        default=Level.SILVER,
        unique=True,
        verbose_name="Уровень"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )

    income_growth_year = models.FloatField(
        default=0.0,
        verbose_name="Рост дохода за год (руб.)"
    )
    mortgage_saving_year = models.FloatField(
        default=0.0,
        verbose_name="Экономия на ипотеке за год (руб.)"
    )
    other_benefit_year = models.FloatField(
        default=0.0,
        verbose_name="Прочие выгоды за год (руб.)"
    )

    title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Заголовок"
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Описание"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлено"
    )
    
    bonus_income_year = models.FloatField(
        default=0.0,
        verbose_name='Годовой доход от бонусов (руб.)'
    )
    mortgage_saving_year = models.FloatField(
        default=0.0,
        verbose_name='Годовая экономия по ипотеке (руб.)'
    )
    cashback_year = models.FloatField(
        default=0.0,
        verbose_name='Годовой кэшбэк (руб.)'
    )
    dms_cost_year = models.FloatField(
        default=0.0,
        verbose_name='Годовые затраты на ДМС (руб.)'
    )

    class Meta:
        verbose_name = "Льгота уровня"
        verbose_name_plural = "Льготы уровней"

    @property
    def total_benefit_year(self) -> float:
        return (
            self.income_growth_year
            + self.mortgage_saving_year
            + self.other_benefit_year
        )

    def __str__(self):
        return self.level
    
    
class LevelPrivilege(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name='Название привилегии'
    )
    description = models.TextField(
        verbose_name='Описание'
    )
    financial_effect_rub = models.FloatField(
        default=0.0,
        verbose_name='Финансовый эффект (руб.)'
    )
    unlock_level = models.CharField(
        max_length=20,
        choices=Level.choices,
        default=Level.SILVER,
        verbose_name='Уровень разблокировки'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Привилегия уровня'
        verbose_name_plural = 'Привилегии уровней'
        ordering = ['title']



class EmployeeDailyResult(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        verbose_name='Сотрудник'
    )
    date = models.DateField(
        verbose_name='Дата'
    )

    deals_count = models.IntegerField(
        default=0,
        verbose_name='Количество сделок'
    )
    credit_volume = models.FloatField(
        default=0.0,
        verbose_name='Объём кредитов (руб.)'
    )
    extra_products_count = models.IntegerField(
        default=0,
        verbose_name='Количество дополнительных продуктов'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания записи'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата последнего обновления'
    )

    class Meta:
        verbose_name = 'Ежедневный результат сотрудника'
        verbose_name_plural = 'Ежедневные результаты сотрудников'
        unique_together = ('employee', 'date')
        ordering = ['-date', 'employee']

    def __str__(self):
        return f'{self.employee} — {self.date}'