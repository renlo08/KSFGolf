from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from tournaments.forms import TournamentForm
from tournaments.models import Tournament

@login_required
def tournament_list(request):
    current_year = datetime.now().year
    tournaments = Tournament.objects.filter(date__year=current_year)
    return render(request, 'tournaments/list.html', {'object_list': tournaments})


@login_required
def tournament_create(request):
    form = TournamentForm(request.POST or None)
    context = {'form': form}
    if form.is_valid():
        obj = form.save()
        object_list = Tournament.objects.filter(date__year=obj.date)
        return redirect('tournaments:list', kwargs={'object_list': object_list})
    return render(request, 'tournaments/create-update.html', context)


