import datetime
from decimal import Decimal
from http import HTTPStatus
from random import uniform

import pytest
from django.contrib.auth import get_user
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client, TestCase, RequestFactory
from django.urls import reverse

from accounts.models import UserProfile
from accounts.views import login_view, register_view
from app import settings
from tournaments.models import Tournament, Competitor


class TestAccountManagement(TestCase):
    def setUp(self):
        self.valid_user_data = {'username': 'testuser', 'password1': 'password123!', 'password2': 'password123!',
                                'first_name': 'test', 'family_name': 'User', 'email': 'username.valid@validuser.com',
                                'phone_number': '+4915150505050', 'hcp': 23.3}
        self.invalid_user_data = {'username': 'testuser', 'password1': 'password123!', 'password2': 'password987!',
                                  'first_name': 'test', 'family_name': 'User', 'email': 'username.valid@validuser.com',
                                  'phone_number': '+4915150505050', 'hcp': 23.3}
        self.request_factory = RequestFactory()
    
    def tearDown(self):
        self.request_factory = None
        
    @pytest.mark.django_db
    def test_response_when_user_login(self):
        # Use Request factory to simulate a POST request to '/login'
        request = self.request_factory.post('/login', data={
            'username': 'test',
            'password': 'test1234'})
    
        User.objects.create_user('test', 'test@test.com', 'test1234')
    
        # Add session to the request
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
    
        form = AuthenticationForm(data=request.POST)
        assert form.is_valid()  # ensure form is valid
    
        response = login_view(request)
    
        user = get_user(request)
        assert user.is_authenticated
    
        # Check successful redirection
        assert response.status_code == 302
        assert response.url == reverse(settings.LOGIN_REDIRECT_URL)
    
    @pytest.mark.django_db
    def test_login_view_get_request(self):
        client = Client()
        response = client.get('/accounts/login/')
        assert 'form' in response.context

    @pytest.mark.django_db
    def test_register_user_credential(self):
        """
        Test for register_view function with a POST request and a valid form data.
        """
        request = self.request_factory.post('/accounts/register/', self.valid_user_data)

        # Add session to the request
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        request.user = AnonymousUser()
        response = register_view(request)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/'

    @pytest.mark.django_db
    def test_register_invalid_user_credential(self):
        """
        Test for register_view function with a POST request and invalid form data.
        """
        request = self.request_factory.post('/accounts/register/', self.invalid_user_data)
    
        # Add session to the request
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
    
        request.user = AnonymousUser()
        response = register_view(request)
    
        assert response.status_code == 200
    
    @pytest.mark.django_db
    def test_logout_user(self):
        """ Test for logout_view function."""
        # Create the user
        User.objects.create_user('test', 'test@test.com', 'testpassword')
    
        # Instantiate the django test client
        client = Client()
        # Use the client to login the user
        client.login(username='test', password='testpassword')
        user = get_user(client)
        assert user.is_authenticated
    
        # Make a post request to logout
        client.post('/accounts/logout/')
        user = get_user(client)
        assert not user.is_authenticated

    @pytest.mark.django_db
    def test_user_profile_is_registered(self):
        """
        Test for UserProfile.is_registered method.
        """
        # Create user, user profile and tournament objects
        user = User.objects.create_user(username='john', password='test-password')
        user_profile = UserProfile.objects.create(user=user, first_name='John', family_name='Doe',
                                                  phone_number='1234567890')
        tournament = Tournament.objects.create(date=datetime.datetime.now(),
                                               tee_time=datetime.time(10, 30),
                                               hcp_limit=34.0)

        request = self.request_factory.post('/accounts/register/', self.valid_user_data)

        # Add session to the request
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        # Update the request user with the created user
        request.user = user
        response = register_view(request)

        # Register the user to the tournament
        competitor = Competitor.objects.create(
            tournament=tournament,
            user_profile=user_profile,
            hcp=Decimal("%.1f" % uniform(0.0, 54.0))
        )
        tournament.participants.add(competitor.user_profile)

        # Check if the user profile is registered to the tournament
        assert user_profile.is_registered(tournament.pk)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == '/'
