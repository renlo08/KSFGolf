import pytest
from django.contrib.auth import get_user
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, Client
from django.urls import reverse

from accounts.views import login_view, register_view
from app import settings


@pytest.mark.django_db
def test_response_when_user_login():
    # Use RequestFactory to simulate a POST request to '/login'
    factory = RequestFactory()
    request = factory.post('/login', data={
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
def test_login_view_get_request():
    client = Client()
    response = client.get('/accounts/login/')
    assert 'form' in response.context


@pytest.fixture
def valid_user_data():
    return {
        'username': 'testuser',
        'password1': 'password123!',
        'password2': 'password123!'
    }


@pytest.fixture
def invalid_user_data():
    return {
        'username': 'testuser',
        'password1': 'password123!',
        'password2': 'password987!'
    }


@pytest.mark.django_db
def test_register_user_credential(valid_user_data):
    """
    Test for register_view function with a POST request and a valid form data.
    """
    factory = RequestFactory()
    request = factory.post('/accounts/register/', valid_user_data)

    # Add session to the request
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()

    request.user = AnonymousUser()
    response = register_view(request)

    assert response.status_code == 302
    assert response.url == '/'


@pytest.mark.django_db
def test_register_invalid_user_credential(invalid_user_data):
    """
    Test for register_view function with a POST request and invalid form data.
    """
    factory = RequestFactory()
    request = factory.post('/accounts/register/', invalid_user_data)

    # Add session to the request
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()

    request.user = AnonymousUser()
    response = register_view(request)

    assert response.status_code == 200


@pytest.mark.django_db
def test_logout_user():
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


if __name__ == '__main__':
    pytest.main()
