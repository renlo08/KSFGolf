from phonenumber_field import modelfields
from django.db import models

from django.conf import settings


User = settings.AUTH_USER_MODEL


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    family_name = models.CharField(max_length=100)
    department = models.CharField(max_length=20)
    phone_number = modelfields.PhoneNumberField()

    def __str__(self):
        return f'{self.first_name} {self.family_name}'

    def is_registered(self, tournament_pk: int) -> bool:
        # Check if the UserProfile is registered to the tournament using 'competitors' related_name
        return self.competitors.filter(pk=tournament_pk).exists()
