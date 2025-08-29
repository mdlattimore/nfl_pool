from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.username

    def __str__(self):
        return self.email