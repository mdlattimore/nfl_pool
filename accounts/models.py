from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    @property
    def display_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name[0]}."
        return self.username  # fallback if names aren't set

    @property
    def fname(self):
        if self.first_name:
            return f"{self.first_name}"
        else:
            return self.username

    def __str__(self):
        return self.username

    # def __str__(self):
    #     return self.email
