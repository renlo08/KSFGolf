from http import HTTPStatus
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user
from django.test import RequestFactory, TestCase, Client
from django.contrib.auth.models import AnonymousUser, User
from django.urls import reverse
from django.utils import timezone

from app import settings
from tournaments import views
from tournaments.models import Tournament, GolfCourse
import datetime

from tournaments.utils import slugify_instance_str


class ViewsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(username='sup-usr', password='test-superuser')
        self.superuser.is_staff = True
        self.superuser.save()


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
        response = self.client.post(reverse('tournaments:create-tournament'),
                                    data={'date': datetime.datetime(current_year, 1, 1).strftime('%Y-%m-%d'),
                                          'tee_time': datetime.time(8, 0),
                                          'course': GolfCourse.objects.first().id,
                                          'hcp_limit': 34.0}
                                    )
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
        response = self.client.post(reverse('tournaments:create-tournament'),
                                    data={'date': datetime.datetime(current_year, 1, 1).strftime('%Y-%m-%d'),
                                          'tee_time': datetime.time(8, 0),
                                          'course': GolfCourse.objects.first().id,
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

        response = self.client.post(reverse('tournaments:create-tournament'),
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

        response = self.client.post(reverse('tournaments:create-tournament'),
                                    data={'date': timezone.now().strftime('%Y-%m-%d'),
                                          'tee_time': datetime.time(8, 0),
                                          'course': GolfCourse.objects.first().id,
                                          'hcp_limit': 34.0}
                                    )
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/admin/login/?next=/tournaments/create-tournament/'


class TestCreateCourse(ViewsTestCase):

    @pytest.mark.django_db
    def test_create_course_success(self):
        self.client.login(username='sup-usr', password='test-superuser')
        response = self.client.post(reverse('tournaments:create-course'),
                                    data={'name': "Dummy Golf Country Club",
                                          'contact_person': 'John Doe',
                                          'email': 'john.doe@dummy-golf-gc.com',
                                          'address': 'dummy road 100',
                                          'city': "Dummy City",
                                          'zip_code': 70806,
                                          'telephone': '+4915150696384',
                                          'country': 'DE'
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
        self.client.login(username='sup-usr', password='test-superuser')
        response = self.client.post(reverse('tournaments:create-course'),
                                    data={'name': "Dummy Golf Country Club",
                                          'contact_person': 'John Doe',
                                          'email': 'john.doe@dummy-golf-gc.com',
                                          'address': 'dummy road 100',
                                          'city': "Dummy City",
                                          'telephone': '+4915150696384',
                                          'country': 'DE'
                                          })
        assert response.status_code == HTTPStatus.OK

        assert len(Tournament.objects.all()) == 0
        assert 'form' in response.context
        assert ['This field is required.'] == response.context['form'].errors.get('zip_code')

    @pytest.mark.django_db
    def test_create_course_fail_invalid_zip_code(self):
        self.client.login(username='sup-usr', password='test-superuser')
        response = self.client.post(reverse('tournaments:create-course'),
                                    data={'name': "Dummy Golf Country Club",
                                          'contact_person': 'John Doe',
                                          'email': 'john.doe@dummy-golf-gc.com',
                                          'address': 'dummy road 100',
                                          'city': "Dummy City",
                                          'telephone': '+4915150696384',
                                          'zip_code': 1_111_111_111_111,
                                          'country': 'DE'
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
                                          'country': 'DE'
                                          })
        assert response.status_code == HTTPStatus.OK

        assert len(Tournament.objects.all()) == 0
        assert 'form' in response.context
        assert ['Ensure this value is greater than or equal to 0.'] == response.context['form'].errors.get('zip_code')

    @pytest.mark.django_db
    def test_create_course_without_superuser_permission(self):
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
                                          'country': 'DE'
                                          })
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/accounts/login/?next=/tournaments/create-course/'

    @pytest.mark.django_db
    def test_create_tournament_without_staff_permission(self):
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
                                          'country': 'DE'
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

    def test_edit_tournament(self):
        self.client.login(username='sup-usr', password='test-superuser')
        current_year = datetime.datetime.now().year
        url = reverse('tournaments:edit-tournament', args=[self.tournament.slug])
        response = self.client.post(url, data={
            'date': datetime.datetime(current_year, 1, 1).strftime('%Y-%m-%d'),
            'tee_time': datetime.time(9, 0),
            'course': GolfCourse.objects.first().id,
            'hcp_limit': 34.0}
                                    )

        assert response.status_code == HTTPStatus.OK
        assert 'message' in response.context
        assert 'Tournament updated successfully' == response.context['message']

    def test_edit_tournament_invalid_field(self):
        self.client.login(username='sup-usr', password='test-superuser')
        current_year = datetime.datetime.now().year
        url = reverse('tournaments:edit-tournament', args=[self.tournament.slug])
        response = self.client.post(url, data={
            'date': datetime.datetime(current_year, 1, 1).strftime('%Y-%m-%d'),
            'tee_time': datetime.time(9, 0),
            'course': GolfCourse.objects.first().id,
            'hcp_limit': 72.0})

        assert response.status_code == HTTPStatus.OK
        templates = [template.name for template in response.templates]
        assert 'tournaments/create-update.html' in templates
        assert 'form' in response.context

    def test_edit_tournament_invalid_slug(self):
        self.client.login(username='sup-usr', password='test-superuser')
        current_year = datetime.datetime.now().year
        url = reverse('tournaments:edit-tournament', args=['invalid-tournament-slug'])
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

    def test_delete_with_unique_tournament_selected(self):
        response = self.client.post(reverse('tournaments:delete-tournaments'),
                                    data={'delete-checkboxes': [self.tournament1.id]})

        # tournament 1 has been deleted.
        assert response.status_code == HTTPStatus.FOUND
        assert not Tournament.objects.filter(id=self.tournament1.id).exists()
        assert Tournament.objects.filter(id=self.tournament2.id).exists()
        assert Tournament.objects.filter(id=self.tournament3.id).exists()
        assert Tournament.objects.filter(id=self.tournament4.id).exists()

    def test_delete_multiple_tournament_selected(self):
        response = self.client.post(reverse('tournaments:delete-tournaments'),
                                    data={'delete-checkboxes': [self.tournament1.id, self.tournament2.id]})

        # Both tournament has been deleted.
        assert response.status_code == HTTPStatus.FOUND
        assert not Tournament.objects.filter(id=self.tournament1.id).exists()
        assert not Tournament.objects.filter(id=self.tournament2.id).exists()
        assert Tournament.objects.filter(id=self.tournament3.id).exists()
        assert Tournament.objects.filter(id=self.tournament4.id).exists()

    def test_delete_without_tournament_selected(self):
        response = self.client.post(reverse('tournaments:delete-tournaments'),
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

        response = self.client.post(reverse('tournaments:delete-tournaments'),
                                    data={'delete-checkboxes': [self.tournament1.id]})
        assert response.status_code == HTTPStatus.FOUND

        # The tournament should not be deleted
        assert Tournament.objects.filter(id=self.tournament1.id).exists()

    def test_delete_fail_no_staff_permission(self):
        # Revoke staff permission from superuser
        self.superuser.is_staff = False
        self.superuser.save()

        response = self.client.post(reverse('tournaments:delete-tournaments'),
                                    data={'delete-checkboxes': [self.tournament1.id]})

        assert response.status_code == HTTPStatus.FOUND
        # The tournament should not be deleted
        assert Tournament.objects.filter(id=self.tournament1.id).exists()
