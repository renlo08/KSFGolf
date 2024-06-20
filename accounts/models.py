from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from phonenumber_field import modelfields
from django.db import models

from django.conf import settings

from tournaments.models import Tournament

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
        tournament = get_object_or_404(Tournament, pk=tournament_pk)
        return self in tournament.participants.all()
