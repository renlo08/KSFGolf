from decimal import Decimal
from http import HTTPStatus
from random import uniform, choice, sample

import pytest
from django.contrib.auth import get_user
from django.test import RequestFactory, TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker

from accounts.models import UserProfile
from tournaments.models import Tournament, GolfCourse, Competitor
import datetime

from tournaments.utils import slugify_instance_str


class ViewsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(username='sup-usr', password='test-superuser',
                                                       email='super.user@superuser.com')
        self.superuser.is_staff = True
        self.superuser.save()
        self.superuser_profile = UserProfile.objects.create(
            user=self.superuser, first_name='Super', family_name='User', phone_number='+4915150505050')


class TestListTournament(ViewsTestCase):
    def setUp(self):
        super().setUp()
        self.golf_course = GolfCourse.objects.create(name='Test golf course', zip_code=70686)

    def test_list_tournament_authenticated(self):
        # request = self.factory.get('')
        # request.user = user

        current_year = datetime.datetime.now().year
        Tournament.objects.create(
            date=datetime.datetime(current_year, 1, 1),
            tee_time=datetime.time(8, 0),
            course=self.golf_course,
            hcp_limit=34.0
        )

        user = User.objects.create_user(username='test', password='test')
        client = Client()
        client.login(username='test', password='test')
        response = client.get('/tournaments/')

        assert response.status_code == 200
        assert 'object_list' in response.context
        assert 'current_year' in response.context
        assert response.context['current_year'] == current_year
        assert len(response.context['object_list']) == 1

    def test_list_tournament_unauthenticated(self):
        client = Client()
        client.login(username='test', password='test')
        response = client.get('/tournaments/')

        assert response.status_code == 302  # Redirection to login page
        assert response.url == '/accounts/login/?next=/tournaments/'

    def test_list_tournament_no_tournaments(self):
        user = User.objects.create_user(username='test', password='test')
        client = Client()
        client.login(username='test', password='test')
        response = client.get('/tournaments/')

        assert response.status_code == 200
        assert 'object_list' in response.context
        assert len(response.context['object_list']) == 0

    @pytest.mark.django_db
    def test_list_tournament_multiple_tournaments(self):
        current_year = datetime.datetime.now().year
        Tournament.objects.create(
            date=datetime.datetime(current_year, 1, 1),
            tee_time=datetime.time(8, 0),
            course=self.golf_course,
            hcp_limit=34.0
        )
        Tournament.objects.create(
            date=datetime.datetime(current_year, 1, 2),
            tee_time=datetime.time(8, 0),
            course=self.golf_course,
            hcp_limit=34.0
        )

        Tournament.objects.create(
            date=datetime.datetime(current_year - 1, 1, 2),
            tee_time=datetime.time(8, 0),
            course=self.golf_course,
            hcp_limit=34.0
        )

        user = User.objects.create_user(username='test', password='test')
        client = Client()
        client.login(username='test', password='test')
        response = client.get('/tournaments/')

        assert response.status_code == 200
        assert 'object_list' in response.context
        assert len(response.context['object_list']) == 2  # only the tournament of the current year


class TestCreateTournament(ViewsTestCase):
    def setUp(self):
        super().setUp()
        self.golf_course = GolfCourse.objects.create(name='Test golf course', zip_code=70686)

    @pytest.mark.django_db
    def test_create_tournament_success(self):
        self.client.login(username='sup-usr', password='test-superuser')
        current_year = datetime.datetime.now().year
        response = self.client.post(reverse('tournaments:create'),
                                    data={'date': datetime.datetime(current_year, 1, 1).strftime('%Y-%m-%d'),
                                          'tee_time': datetime.time(8, 0),
                                          'course': GolfCourse.objects.first().id,
                                          'hcp_limit': 34.0,
                                          'max_participants': 30})
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse('tournaments:list')

        qs = Tournament.objects.all()
        assert qs.count() == 1
        tournament = qs.first()
        assert tournament.slug == 'test-golf-course-2024-01-01'

    @pytest.mark.django_db
    def test_create_tournament_fail(self):
        self.client.login(username='sup-usr', password='test-superuser')
        current_year = datetime.datetime.now().year
        response = self.client.post(reverse('tournaments:create'),
                                    data={'date': datetime.datetime(current_year, 1, 1).strftime('%Y-%m-%d'),
                                          'tee_time': datetime.time(8, 0),
                                          'course': GolfCourse.objects.first().id,
                                          'max_participants': 30
                                          })
        assert response.status_code == HTTPStatus.OK

        assert len(Tournament.objects.all()) == 0
        assert 'form' in response.context
        assert {'hcp_limit': ['This field is required.']} == response.context['form'].errors

    @pytest.mark.django_db
    def test_create_tournament_without_superuser_permission(self):
        staff_usr = User.objects.create_user(username='staff_usr', password='staff')
        staff_usr.is_staff = True
        staff_usr.save()
        self.client.login(username='staff_usr', password='staff')
        user = get_user(self.client)
        assert user.is_superuser is False
        assert user.is_staff is True

        response = self.client.post(reverse('tournaments:create'),
                                    data={'date': timezone.now().strftime('%Y-%m-%d'),
                                          'tee_time': datetime.time(8, 0),
                                          'course': GolfCourse.objects.first().id,
                                          'hcp_limit': 34.0}
                                    )
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/accounts/login/?next=/tournaments/create-tournament/'

    @pytest.mark.django_db
    def test_create_tournament_without_staff_permission(self):
        # revoke staff permission to superuser
        self.superuser.is_staff = False
        self.superuser.save()
        self.client.login(username='sup-usr', password='test-superuser')

        response = self.client.post(reverse('tournaments:create'),
                                    data={'date': timezone.now().strftime('%Y-%m-%d'),
                                          'tee_time': datetime.time(8, 0),
                                          'course': GolfCourse.objects.first().id,
                                          'hcp_limit': 34.0}
                                    )
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/admin/login/?next=/tournaments/create-tournament/'


class TestCreateCourse(ViewsTestCase):

    def setUp(self):
        super().setUp()
        self.client.login(username='sup-usr', password='test-superuser')

    @pytest.mark.django_db
    def test_create_course_success(self):
        response = self.client.post(reverse('tournaments:create-course'),
                                    data={'name': "Dummy Golf Country Club",
                                          'contact_person': 'John Doe',
                                          'email': 'john.doe@dummy-golf-gc.com',
                                          'address': 'dummy road 100',
                                          'city': "Dummy City",
                                          'zip_code': 70806,
                                          'telephone': '+4915150696384',
                                          'country': 'DE',
                                          'greenfee_external':80,
                                          'greenfee_member': 15
                                          })
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse('tournaments:list')

        qs = GolfCourse.objects.all()
        assert qs.count() == 1
        course = qs.first()
        assert str(course) == 'Dummy Golf Country Club'
        assert course.country == 'DE'

    @pytest.mark.django_db
    def test_create_course_fail_required_field(self):
        response = self.client.post(reverse('tournaments:create-course'),
                                    data={'name': "Dummy Golf Country Club",
                                          'contact_person': 'John Doe',
                                          'email': 'john.doe@dummy-golf-gc.com',
                                          'address': 'dummy road 100',
                                          'city': "Dummy City",
                                          'telephone': '+4915150696384',
                                          'country': 'DE',
                                          'greenfee_external': 80,
                                          'greenfee_member': 15
                                          })
        assert response.status_code == HTTPStatus.OK

        assert len(Tournament.objects.all()) == 0
        assert 'form' in response.context
        assert ['This field is required.'] == response.context['form'].errors.get('zip_code')

    @pytest.mark.django_db
    def test_create_course_fail_invalid_zip_code(self):
        response = self.client.post(reverse('tournaments:create-course'),
                                    data={'name': "Dummy Golf Country Club",
                                          'contact_person': 'John Doe',
                                          'email': 'john.doe@dummy-golf-gc.com',
                                          'address': 'dummy road 100',
                                          'city': "Dummy City",
                                          'telephone': '+4915150696384',
                                          'zip_code': 1_111_111_111_111,
                                          'country': 'DE',
                                          'greenfee_external': 80,
                                          'greenfee_member': 15
                                          })
        assert response.status_code == HTTPStatus.OK

        assert len(Tournament.objects.all()) == 0
        assert 'form' in response.context
        assert ['Ensure this value is less than or equal to 99999.'] == response.context['form'].errors.get('zip_code')

        response = self.client.post(reverse('tournaments:create-course'),
                                    data={'name': "Dummy Golf Country Club",
                                          'contact_person': 'John Doe',
                                          'email': 'john.doe@dummy-golf-gc.com',
                                          'address': 'dummy road 100',
                                          'city': "Dummy City",
                                          'telephone': '+4915150696384',
                                          'zip_code': -1_111_111_111_111,
                                          'country': 'DE',
                                          'greenfee_external': 80,
                                          'greenfee_member': 15
                                          })
        assert response.status_code == HTTPStatus.OK

        assert len(Tournament.objects.all()) == 0
        assert 'form' in response.context
        assert ['Ensure this value is greater than or equal to 0.'] == response.context['form'].errors.get('zip_code')

    @pytest.mark.django_db
    def test_create_course_without_superuser_permission(self):
        self.client.logout()
        staff_usr = User.objects.create_user(username='staff_usr', password='staff')
        staff_usr.is_staff = True
        staff_usr.save()
        self.client.login(username='staff_usr', password='staff')
        user = get_user(self.client)
        assert user.is_superuser is False
        assert user.is_staff is True

        response = self.client.post(reverse('tournaments:create-course'),
                                    data={'name': "Dummy Golf Country Club",
                                          'contact_person': 'John Doe',
                                          'email': 'john.doe@dummy-golf-gc.com',
                                          'address': 'dummy road 100',
                                          'city': "Dummy City",
                                          'zip_code': 70806,
                                          'telephone': '+4915150696384',
                                          'country': 'DE',
                                          'greenfee_external': 80,
                                          'greenfee_member': 15
                                          })
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/accounts/login/?next=/tournaments/create-course/'

    @pytest.mark.django_db
    def test_create_tournament_without_staff_permission(self):
        self.client.logout()
        # revoke staff permission to superuser
        self.superuser.is_staff = False
        self.superuser.save()
        self.client.login(username='sup-usr', password='test-superuser')

        response = self.client.post(reverse('tournaments:create-course'),
                                    data={'name': "Dummy Golf Country Club",
                                          'contact_person': 'John Doe',
                                          'email': 'john.doe@dummy-golf-gc.com',
                                          'address': 'dummy road 100',
                                          'city': "Dummy City",
                                          'zip_code': 70806,
                                          'telephone': '+4915150696384',
                                          'country': 'DE',
                                          'greenfee_external': 80,
                                          'greenfee_member': 15
                                          })

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/admin/login/?next=/tournaments/create-course/'


class TestEditTournament(ViewsTestCase):

    def setUp(self):
        super().setUp()
        current_year = datetime.datetime.now().year
        self.golf_course = GolfCourse.objects.create(
            name="Dummy Golf Country Club",
            contact_person='John Doe',
            email='john.doe@dummy-golf-gc.com',
            address='dummy road 100',
            city="Dummy City",
            zip_code=70806,
            telephone='+4915150696384',
            country='DE')
        self.tournament = Tournament.objects.create(
            date=datetime.datetime(current_year, 1, 1),
            tee_time=datetime.time(8, 0),
            course=self.golf_course,
            hcp_limit=34.0
        )
        slugify_instance_str(self.tournament, save=True)

    @pytest.mark.django_db
    def test_edit_tournament(self):
        self.client.login(username='sup-usr', password='test-superuser')
        current_year = datetime.datetime.now().year
        url = self.tournament.get_edit_url()
        response = self.client.post(url, data={
            'date': datetime.datetime(current_year, 1, 1).strftime('%Y-%m-%d'),
            'tee_time': datetime.time(9, 0),
            'course': GolfCourse.objects.first().id,
            'hcp_limit': 34.0,
            'max_participants': 30})
        assert response.status_code == HTTPStatus.OK
        assert 'message' in response.context
        assert 'Tournament updated successfully' == response.context['message']

    @pytest.mark.django_db
    def test_edit_tournament_relevant_slug_field(self):
        another_course = GolfCourse.objects.create(
            name="Another Dummy Golf Country Club",
            contact_person='John Doe',
            email='john.doe@dummy-golf-gc.com',
            address='dummy road 100',
            city="Dummy City",
            zip_code=70806,
            telephone='+4915150505050',
            country='DE')

        self.client.login(username='sup-usr', password='test-superuser')
        url = self.tournament.get_edit_url()
        current_year = datetime.datetime.now().year
        response = self.client.post(
            url,
            data={'course': another_course.id,
                  'date': datetime.datetime(current_year, 1, 1).strftime('%Y-%m-%d'),
                  'hcp_limit': 34.0,
                  'max_participants': 30})
        assert response.status_code == HTTPStatus.OK
        assert 'Tournament updated successfully' == response.context['message']
        # slug is getting updated (no tournament creation)
        assert Tournament.objects.count() == 1
        assert Tournament.objects.first().slug == 'another-dummy-golf-country-club-2024-01-01'

    def test_edit_tournament_invalid_field(self):
        self.client.login(username='sup-usr', password='test-superuser')
        current_year = datetime.datetime.now().year
        url = self.tournament.get_edit_url()
        response = self.client.post(url, data={
            'date': datetime.datetime(current_year, 1, 1).strftime('%Y-%m-%d'),
            'tee_time': datetime.time(9, 0),
            'course': GolfCourse.objects.first().id,
            'hcp_limit': 72.0})

        assert response.status_code == HTTPStatus.OK
        templates = [template.name for template in response.templates]
        assert 'tournaments/create-update.html' in templates
        assert 'form' in response.context

    def test_edit_tournament_fail_invalid_pk(self):
        self.client.login(username='sup-usr', password='test-superuser')
        current_year = datetime.datetime.now().year
        # request a not existing pk = 500 000
        url = reverse('tournaments:edit', args=[500_000])
        response = self.client.post(url, data={
            'date': datetime.datetime(current_year, 1, 1).strftime('%Y-%m-%d'),
            'tee_time': datetime.time(9, 0),
            'course': GolfCourse.objects.first().id,
            'hcp_limit': 72.0})

        assert response.status_code == HTTPStatus.NOT_FOUND


class TestDeleteTournament(ViewsTestCase):
    def setUp(self):
        super().setUp()

        # Log in the superuser
        self.client.login(username='sup-usr', password='test-superuser')

        # Create a dummy golf course
        self.golf_course = GolfCourse.objects.create(name='Test golf course', zip_code=70686)
        # Create some dummy tournaments for testing
        current_year = datetime.datetime.now().year
        common_data = {'date': timezone.now().strftime('%Y-%m-%d'),
                       'tee_time': datetime.time(8, 0),
                       'course': self.golf_course}

        self.tournament1 = Tournament.objects.create(hcp_limit=12.0, **common_data)
        self.tournament2 = Tournament.objects.create(hcp_limit=13.0, **common_data)
        self.tournament3 = Tournament.objects.create(hcp_limit=14.0, **common_data)
        self.tournament4 = Tournament.objects.create(hcp_limit=15.0, **common_data)

    @pytest.mark.django_db
    def test_delete_with_unique_tournament_selected(self):
        response = self.client.post(reverse('tournaments:delete'),
                                    data={'delete-checkboxes': [self.tournament1.id]})

        # tournament 1 has been deleted.
        assert response.status_code == HTTPStatus.FOUND
        assert not Tournament.objects.filter(id=self.tournament1.id).exists()
        assert Tournament.objects.filter(id=self.tournament2.id).exists()
        assert Tournament.objects.filter(id=self.tournament3.id).exists()
        assert Tournament.objects.filter(id=self.tournament4.id).exists()

    @pytest.mark.django_db
    def test_delete_multiple_tournament_selected(self):
        response = self.client.post(reverse('tournaments:delete'),
                                    data={'delete-checkboxes': [self.tournament1.id, self.tournament2.id]})

        # Both tournament has been deleted.
        assert response.status_code == HTTPStatus.FOUND
        assert not Tournament.objects.filter(id=self.tournament1.id).exists()
        assert not Tournament.objects.filter(id=self.tournament2.id).exists()
        assert Tournament.objects.filter(id=self.tournament3.id).exists()
        assert Tournament.objects.filter(id=self.tournament4.id).exists()

    @pytest.mark.django_db
    def test_delete_without_tournament_selected(self):
        response = self.client.post(reverse('tournaments:delete'),
                                    data={})
        self.assertEqual(response.status_code, 302)  # HTTPStatus.FOUND
        # No tournament should be deleted
        assert response.status_code == HTTPStatus.FOUND
        assert Tournament.objects.filter(id=self.tournament1.id).exists()
        assert Tournament.objects.filter(id=self.tournament2.id).exists()
        assert Tournament.objects.filter(id=self.tournament3.id).exists()
        assert Tournament.objects.filter(id=self.tournament4.id).exists()

    def test_delete_fail_no_superuser_permission(self):
        # Create a non-superuser staff member for this test
        staff_user = User.objects.create_user(username='staff', password='test-staff')
        staff_user.is_staff = True
        staff_user.save()

        self.client.login(username='staff', password='test-staff')

        response = self.client.post(reverse('tournaments:delete'),
                                    data={'delete-checkboxes': [self.tournament1.id]})
        assert response.status_code == HTTPStatus.FOUND

        # The tournament should not be deleted
        assert Tournament.objects.filter(id=self.tournament1.id).exists()

    def test_delete_fail_no_staff_permission(self):
        # Revoke staff permission from superuser
        self.superuser.is_staff = False
        self.superuser.save()

        response = self.client.post(reverse('tournaments:delete'),
                                    data={'delete-checkboxes': [self.tournament1.id]})

        assert response.status_code == HTTPStatus.FOUND
        # The tournament should not be deleted
        assert Tournament.objects.filter(id=self.tournament1.id).exists()


class TestTournamentDetail(ViewsTestCase):

    def setUp(self):
        super().setUp()

        # Log in the superuser
        self.client.login(username='sup-usr', password='test-superuser')

        current_year = datetime.datetime.now().year
        self.golf_course = GolfCourse.objects.create(
            name="Dummy Golf Country Club",
            contact_person='John Doe',
            email='john.doe@dummy-golf-gc.com',
            address='dummy road 100',
            city="Dummy City",
            zip_code=70806,
            telephone='+4915150696384',
            country='DE')
        self.tournament = Tournament.objects.create(
            date=datetime.datetime(current_year, 1, 1),
            tee_time=datetime.time(8, 0),
            course=self.golf_course,
            hcp_limit=34.0
        )
        slugify_instance_str(self.tournament, save=True)

    @pytest.mark.django_db
    def test_show_tournament_overview(self):
        response = self.client.get(reverse('tournaments:detail', kwargs={'pk': self.tournament.id, 'detail_page': 'overview'}))
        assert response.status_code == HTTPStatus.OK
        assert response.context.get('detail_template') == 'tournaments/partials/overview.html'
        assert response.context.get('object') == self.tournament
        assert response.context.get('course') == self.golf_course
        assert not response.context.get('is_registered')

    def test_show_tournament_overview_fail_login_required(self):
        # log out the user
        self.client.logout()
        response = self.client.get(reverse('tournaments:detail', kwargs={'pk': self.tournament.id, 'detail_page': 'overview'}))
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/accounts/login/?next=/tournaments/1/overview'

    @pytest.mark.django_db
    def test_show_registered_participants(self):
        response = self.client.post(reverse('tournaments:detail', kwargs={'pk': self.tournament.id, 'detail_page': 'participants'}))
        assert response.context.get('detail_template') == 'tournaments/partials/participants.html'
        context_object = response.context
        assert context_object.get('object') == self.tournament
        assert context_object.get('course') == self.golf_course
        assert not context_object.get('is_registered')
        assert self.superuser_profile not in context_object.get('competitors').all()

        # click to register the participation
        response = self.client.post(reverse('accounts:participate', args=[self.tournament.id]))
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/tournaments/1/overview'
        # Make sure that a competitor exist.
        assert Competitor.objects.get(tournament=self.tournament, user_profile=self.superuser_profile)

    def test_show_tournament_participants_fail_staff_permission_required(self):
        # Revoke staff permission from superuser
        self.superuser.is_staff = False
        self.superuser.save()

        response = self.client.post(reverse('tournaments:detail', kwargs={'pk': self.tournament.id, 'detail_page': 'participants'}))
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/tournaments/1/overview'

    def test_show_tournament_participants_fail_login_required(self):
        self.client.logout()
        response = self.client.post(reverse('tournaments:detail', kwargs={'pk': self.tournament.id, 'detail_page': 'participants'}))
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/accounts/login/?next=/tournaments/1/participants'

    @pytest.mark.django_db
    def test_register_to_tournament(self):
        assert self.tournament.participants.count() == 0
        response = self.client.post(reverse('accounts:participate', kwargs={'pk': self.tournament.pk}))
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/tournaments/1/overview'
        assert self.tournament.participants.count() == 1

    def test_register_to_tournament_fail_login_required(self):
        # log out the user
        self.client.logout()
        response = self.client.post(reverse('accounts:participate', kwargs={'pk': self.tournament.pk}))
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/accounts/login/?next=/accounts/1/participate/'

    @pytest.mark.django_db
    def test_revoke_tournament_participation(self):
        # prepare the test and add the user to the tournament
        self.tournament.participants.clear()
        competitor = Competitor.objects.create(
            tournament=self.tournament,
            user_profile=self.superuser_profile,
            hcp=Decimal("%.1f" % uniform(0.0, 54.0))
        )
        self.tournament.participants.add(competitor.user_profile)
        assert self.tournament.participants.count() == 1

        # simulate the revokation
        response = self.client.post(reverse('accounts:participate', kwargs={'pk': self.tournament.pk}))
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/tournaments/1/overview'

    def test_revoke_tournament_participation_fail_login_required(self):
        # prepare the test and add the user to the tournament
        self.tournament.participants.clear()
        competitor = Competitor.objects.create(
            tournament=self.tournament,
            user_profile=self.superuser_profile,
            hcp=Decimal("%.1f" % uniform(0.0, 54.0))
        )
        self.tournament.participants.add(competitor.user_profile)
        assert self.tournament.participants.count() == 1
        self.client.logout()

        # simulate the revokation
        response = self.client.post(reverse('accounts:participate', kwargs={'pk': self.tournament.pk}))
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/accounts/login/?next=/accounts/1/participate/'


class TestTournamentSetup(TestCase):
    @classmethod
    def setUpTestData(cls):
        fake = Faker('de_DE')  # German local

        # create 100 UserProfile
        # Generate 100 User instances and UserProfile instances
        for i in range(100):
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

            # create a golf course
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

            # Create a tournament
            all_user_profiles = UserProfile.objects.all()
            Tournament.objects.create(
                date=fake.date_time_this_year(before_now=True, after_now=True, tzinfo=None),
                tee_time=fake.time_object(),
                course=GolfCourse.objects.first(),
                supervisor=choice(all_user_profiles),
                hcp_limit=Decimal("%.1f" % uniform(0.0, 54.0)),
                hcp_relevant=fake.boolean(),
                comment=fake.text())

    def setUp(self):
        # add a multiple of 3 of number of participants (30 participants)
        all_participants = UserProfile.objects.all()
        participants = sample(list(all_participants), 30)
        self.tournament = Tournament.objects.first()
        for participant in participants:
            Competitor.objects.create(
                tournament=self.tournament,
                user_profile=participant,
                hcp=Decimal("%.1f" % uniform(0.0, 54.0))
            )
        self.tournament.save()

    def tearDown(self):
        # Remove the participants from the tournament
        tournament = Tournament.objects.first()
        tournament.participants.clear()


class TestTournamentPreparation(TestTournamentSetup):

    @pytest.mark.django_db
    def test_generate_flight_by_handicap(self):
        response = self.client.get(reverse('tournaments:fetch_flights'), {'tpk': self.tournament.pk})
        flights = response.context.get('flights')

        assert flights is not None, "No flights found in response context"

        for flight in flights:
            hcp_values = [competitor.hcp for competitor in flight]
            # Check if 'hcp' values are  in ascending order
            assert hcp_values == sorted(hcp_values), "Competitors in a flight are not ordered by 'hcp'"
