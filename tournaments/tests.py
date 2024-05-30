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


class TestListTournament(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
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


class TestCreateTournament(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(username='sup-usr', password='test-superuser')
        self.superuser.is_staff = True
        self.superuser.save()
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
        tournament = qs.first()
        assert tournament.slug == 'test-golf-course-2024-01-01'
        assert len(qs) == 1

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


# TODO create test of edit tournament, delete tournaments, create course