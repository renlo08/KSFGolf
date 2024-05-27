import datetime

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class GolfCourse(models.Model):
    GERMANY = "DE"
    ENGLAND = "EN"
    FRANCE = "FR"
    COUNTRY_CHOICES = {
        GERMANY: "Germany",
        ENGLAND: "England",
        FRANCE: "France",
    }
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    telephone = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    address = models.CharField(max_length=100)
    zip_code = models.IntegerField(validators=[MinValueValidator(00000), MaxValueValidator(99999)])
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default=GERMANY)


class Tournament(models.Model):
    id = models.IntegerField(primary_key=True)
    creation_date = models.DateField(auto_now_add=True)
    updated_date = models.DateField(auto_now=True)
    date = models.DateField(default=timezone.now)
    tee_time = models.TimeField(null=True, blank=True, default=datetime.time(9, 0))
    course = models.ManyToManyField(GolfCourse, null=True, blank=True)
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    hcp_limit = models.DecimalField(max_digits=3, decimal_places=1, null=False,
                                    validators=[MinValueValidator(0.0), MaxValueValidator(54.0)])
