from django.db import models


class Status(models.TextChoices):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class BookingModels(models.Model):
    user_id = models.PositiveIntegerField()
    event_id = models.PositiveIntegerField()
    created_at = models.DateField(auto_now_add=True)

    status = models.CharField(choices=Status, default=Status.PENDING)
