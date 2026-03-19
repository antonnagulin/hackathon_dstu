from django.db import models


class EventModels(models.Model):
    title = models.CharField("Название")
    description = models.TextField("Описание")
    capacity = models.PositiveIntegerField("Свободных мест")
    date = models.DateTimeField("Дата и время ивента")
