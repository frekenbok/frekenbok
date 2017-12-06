from django.contrib.auth.models import User
from django.db import models


class TelegramUser(models.Model):
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name='telegram_username'
    )
    username = models.CharField(max_length=255)
