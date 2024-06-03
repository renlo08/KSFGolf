import datetime

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class GolfCourse(models.Model):
    GERMANY = "DE"
    ENGLAND = "EN"
    FRANCE = "FR"
    COUNTRY_CHOICES = [
        (GERMANY, "Germany"),
        (ENGLAND, "England"),
        (FRANCE, "France"),
    ]
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    telephone = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    address = models.CharField(max_length=100)
    zip_code = models.IntegerField(validators=[MinValueValidator(00000), MaxValueValidator(99999)])
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default=GERMANY)

    def __str__(self):
        return self.name

    def get_full_city(self):
        return f"{self.country}-{self.zip_code} {self.city}"


class Tournament(models.Model):
    id = models.AutoField(primary_key=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    creation_date = models.DateField(auto_now_add=True)
    updated_date = models.DateField(auto_now=True)
    date = models.DateField(default=timezone.now)
    tee_time = models.TimeField(null=True, blank=True, default=datetime.time(9, 0))
    course = models.ForeignKey(GolfCourse, null=True, blank=True, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    hcp_limit = models.DecimalField(max_digits=3, decimal_places=1, null=False,
                                    validators=[MinValueValidator(0.0), MaxValueValidator(54.0)])
    hcp_relevant = models.BooleanField(default=True)
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.course}: {self.date.strftime('%Y-%m-%d')}"

    def get_absolute_url(self):
        return reverse("tournaments:detail", kwargs={"slug": self.slug, "detail_page": 'overview'})

    def get_edit_url(self):
        return reverse("tournaments:edit", kwargs={"slug": self.slug})

    def back(self):
        return reverse("tournaments:list")
