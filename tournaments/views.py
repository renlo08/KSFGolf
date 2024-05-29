from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from tournaments.forms import TournamentForm, GolfCourseForm
from tournaments.models import Tournament
from tournaments.utils import slugify_instance_str


@login_required
def list_tournament(request):
    current_year = datetime.now().year
    tournament_qs = Tournament.objects.filter(date__year=current_year).order_by('date')
    return render(request, 'tournaments/list.html', {'object_list': tournament_qs})


@user_passes_test(lambda usr: usr.is_superuser)
@staff_member_required
def create_tournament(request):
    form = TournamentForm(request.POST or None)
    context = {'form': form}
    if form.is_valid():
        tournament = form.save(commit=False)
        tournament.slug = slugify_instance_str(tournament, save=True)
        current_year = datetime.now().year
        tournament_qs = Tournament.objects.filter(date__year=current_year)
        # return redirect('tournaments:list', kwargs={'object_list': tournament_qs})
        return redirect('tournaments:list')
    return render(request, 'tournaments/create-update.html', context)


@user_passes_test(lambda usr: usr.is_superuser)
@staff_member_required
def create_course(request):
    form = GolfCourseForm(request.POST or None)
    context = {'form': form}
    if form.is_valid():
        form.save()
        current_year = datetime.now().year
        tournament_qs = Tournament.objects.filter(date__year=current_year)
        return HttpResponseRedirect(reverse('tournaments:list', kwargs={'object_list': tournament_qs}))
        # return redirect('tournaments:list', context={'object_list': tournament_qs})
    return render(request, 'tournaments/create-update.html', context)


@user_passes_test(lambda usr: usr.is_superuser)
@staff_member_required
def edit_tournament(request, slug=None):
    obj = get_object_or_404(Tournament, slug=slug)
    form = TournamentForm(request.POST or None, instance=obj)
    context = {
        "form": form,
    }
    if form.is_valid():
        form.save()
        context['message'] = 'Tournament updated successfully'
    # if request.htmx:
    #     return render(request, "recipes/partials/forms.html", context)
    return render(request, "tournaments/create-update.html", context)
