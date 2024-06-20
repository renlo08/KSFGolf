from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from accounts.forms import UserRegistrationForm
from accounts.models import UserProfile
from app import settings
from tournaments.models import Tournament, Competitor


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
    user_profile = UserProfile.objects.get(user=request.user)

    if request.method == 'POST':
        # identify the participation of the user to the tournament
        competitor_instance = Competitor.objects.filter(tournament=tournament, user_profile=user_profile).first()
        if competitor_instance:
            # remove the user from the participant
            competitor_instance.delete()
        else:
            # add the user to the participant
            Competitor.objects.create(
                tournament=tournament,
                user_profile=user_profile,
                registration_date=timezone.now().date(),
                hcp=54.0  # TODO: create new registration form
            )
    return redirect('tournaments:detail', pk=tournament.pk, detail_page='overview')