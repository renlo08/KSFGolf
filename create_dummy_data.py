import os
from datetime import timedelta

import django

import logging

from decimal import Decimal
from random import uniform, choice, random, randint, sample

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
django.setup()

from django.contrib.auth.models import User
from django.utils.text import slugify
from faker import Faker

from accounts.models import UserProfile
from tournaments.models import Tournament, GolfCourse, Competitor

# creating a logging instance with the name 'MyLogger'
logger = logging.getLogger('MyLogger')
logger.setLevel(logging.DEBUG)

# setting up logging to console
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

# creating logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# adding handler to the logger
logger.addHandler(handler)

fake = Faker('de_DE')  # German local

from django.core.management import call_command

logger.info("Deleting all model instances")

# to flush all models
call_command('flush', '--noinput')

# Or to delete all records in a model
GolfCourse.objects.all().delete()
Tournament.objects.all().delete()
UserProfile.objects.all().delete()

NR_INSTANCE = 10

logger.info(f"Creating super user")
username = 'lolo'
email = 'lolofanf1@hotmail.com'
password = 'qwertzuiopü'

superuser = User.objects.create_superuser(username=username, email=email, password=password)
UserProfile.objects.create(
    user=superuser,
    first_name='Laurent',
    family_name='Bihin',
    phone_number=fake.phone_number(),
    department=fake.company()
)

logger.info(f"Creating {NR_INSTANCE} User instance")
# Generate 100 User instances
for _ in range(NR_INSTANCE):
    User.objects.create_user(username=fake.user_name(),
                             email=fake.email(),
                             password=fake.password(length=10,
                                                    special_chars=True,
                                                    digits=True,
                                                    upper_case=True,
                                                    lower_case=True))

logger.info(f"Creating {NR_INSTANCE} UserProfiles")

# Generate 100 User instances and UserProfile instances
for i in range(NR_INSTANCE):
    username = fake.user_name() + str(i)
    user = User.objects.create_user(username=username,
                                    email=fake.email(),
                                    password=fake.password(length=10,
                                                           special_chars=True,
                                                           digits=True,
                                                           upper_case=True,
                                                           lower_case=True))
    # Create a fake UserProfile
    UserProfile.objects.create(
        user=user,
        first_name=fake.first_name(),
        family_name=fake.last_name(),
        phone_number=fake.phone_number(),
        department=fake.company()
    )

logger.info("Creating 10 golf courses")

# Generate 10 golf courses
for _ in range(10):
    GolfCourse.objects.create(
        name=fake.word() + fake.word() + ' golf.e.V',
        contact_person=fake.name(),
        telephone=fake.phone_number(),
        email=fake.email(),
        address=fake.street_address(),
        zip_code=fake.random_int(min=10000, max=99999),
        city=fake.city(),
        country='DE'
    )

all_courses = GolfCourse.objects.all()  # reference to all golf courses
all_user_profiles = UserProfile.objects.all()  # reference to all user profiles

logger.info("Creating 50 tournaments")

# Generate 50 tournaments
for num in range(50):
    tournament = Tournament.objects.create(
        slug=slugify(f"tournament-{num + 1}"),
        date=fake.date_time_this_year(before_now=True, after_now=True, tzinfo=None),
        tee_time=fake.time_object(),
        course=choice(all_courses),
        supervisor=choice(all_user_profiles),
        hcp_limit=Decimal("%.1f" % uniform(0.0, 54.0)),
        hcp_relevant=fake.boolean(),
        comment=fake.text())

    # assume `tournament` is the current tournament instance
    participants_count = randint(0, 30)
    participants_count = min(participants_count, len(all_user_profiles))
    participants = sample(list(all_user_profiles), participants_count)

    for participant in participants:
        # generate a random number of days to subtract from the tournament date
        days_before_tournament = randint(1, 25)

        # calculate the registration_date
        registration_date = tournament.date - timedelta(days=days_before_tournament)

        # create a Competitor instance with the computed registration date
        competitor = Competitor.objects.create(
            tournament=tournament,
            competitor=participant,
            hcp=Decimal("%.1f" % uniform(0.0, 54.0))
        )
        competitor.registration_date = registration_date
        competitor.save()
