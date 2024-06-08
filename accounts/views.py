from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import redirect, render, get_object_or_404

from accounts.forms import UserRegistrationForm
from accounts.models import UserProfile
from app import settings
from tournaments.models import Tournament


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            usr = form.get_user()
            login(request, usr)
            return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        form = AuthenticationForm(request)
    context = {'form': form}
    return render(request, 'accounts/login.html', context)


def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST or None)
        if form.is_valid():
            usr_obj = form.save()

            login(request, usr_obj)
            return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        form = UserRegistrationForm()
    context = {'form': form}
    return render(request, 'accounts/register.html', context)


def logout_view(request):
    logout(request)
    return redirect(settings.LOGIN_REDIRECT_URL)


@login_required
def tournament_registration_view(request, pk: int):
    tournament = get_object_or_404(Tournament, pk=pk)
    if request.method == 'POST':
        # identify the participation of the user to the tournament
        user = UserProfile.objects.get(user=request.user)
        if user in tournament.participants.all():
            # remove the user from the participant
            tournament.participants.remove(user)
        else:
            # add the user to the participant
            tournament.participants.add(user)
    return redirect('tournaments:detail', pk=tournament.pk, detail_page='overview')
