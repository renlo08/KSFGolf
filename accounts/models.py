from django.core.validators import MinValueValidator, MaxValueValidator
from phonenumber_field import modelfields
from django.db import models

from django.conf import settings

User = settings.AUTH_USER_MODEL


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = modelfields.PhoneNumberField()
    hcp = models.DecimalField(max_digits=3, decimal_places=1, null=False,
                              validators=[MinValueValidator(0.0), MaxValueValidator(54.0)])

