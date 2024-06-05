import datetime

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from phonenumber_field import modelfields

from tournaments import utils


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
    telephone = modelfields.PhoneNumberField()
    email = models.EmailField(max_length=100)
    address = models.CharField(max_length=100)
    zip_code = models.IntegerField(validators=[MinValueValidator(00000), MaxValueValidator(99999)])
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default=GERMANY)
    greenfee_external = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    greenfee_member = models.DecimalField(max_digits=4, decimal_places=1, default=0)

    def __str__(self):
        return self.name

    def get_full_city(self):
        return f"{self.country}-{self.zip_code} {self.city}"


class Tournament(models.Model):
    id = models.AutoField(primary_key=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    creation_date = models.DateField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    date = models.DateField(default=timezone.now)
    tee_time = models.TimeField(null=True, blank=True, default=datetime.time(9, 0))
    course = models.ForeignKey(GolfCourse, null=True, blank=True, on_delete=models.CASCADE)
    supervisor = models.ForeignKey('accounts.UserProfile', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='supervising_tournament')
    hcp_limit = models.DecimalField(max_digits=3, decimal_places=1, null=False,
                                    validators=[MinValueValidator(0.0), MaxValueValidator(54.0)])
    hcp_relevant = models.BooleanField(default=True)
    comment = models.TextField(blank=True)
    participants = models.ManyToManyField('accounts.UserProfile', blank=True,
                                          related_name='tournament_participants')

    def __str__(self):
        return f"{self.course}: {self.date.strftime('%Y-%m-%d')}"

    def get_absolute_url(self):
        return reverse("tournaments:detail", kwargs={"pk": self.pk, "detail_page": 'overview'})

    def get_edit_url(self):
        return reverse("tournaments:edit", kwargs={"pk": self.pk})

    def back(self):
        return reverse("tournaments:list")

    def elapsed_time(self):
        return utils.stringify_time_delta(self.updated_date)
