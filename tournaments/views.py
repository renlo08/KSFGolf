from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import UserProfile
from tournaments.forms import TournamentForm, GolfCourseForm
from tournaments.models import Tournament
from tournaments.utils import slugify_instance_str


@login_required
def list_tournament(request):
    filter_type = request.GET.get('type')
    current_year = datetime.now().year
    if filter_type == 'past':
        tournament_qs = Tournament.objects.filter(date__lt=datetime.today()).order_by('date')
    elif filter_type == 'upcoming':
        tournament_qs = Tournament.objects.filter(date__gte=datetime.today()).order_by('date')
    else:
        tournament_qs = Tournament.objects.filter(date__year=current_year).order_by('date')
        pass
    context = {
        'object_list': tournament_qs,
        'current_year': current_year,
    }
    return render(request, 'tournaments/list.html', context)


@user_passes_test(lambda usr: usr.is_superuser)
@staff_member_required
def create_tournament(request):
    form = TournamentForm(request.POST or None)
    context = {'form': form}
    if form.is_valid():
        tournament = form.save(commit=False)
        tournament.slug = slugify_instance_str(tournament, save=True)
        return redirect('tournaments:list')
    return render(request, 'tournaments/create-update.html', context)


@user_passes_test(lambda usr: usr.is_superuser)
@staff_member_required
def create_course(request):
    form = GolfCourseForm(request.POST or None)
    context = {'form': form}
    if form.is_valid():
        form.save()
        return redirect('tournaments:list')
    return render(request, 'tournaments/create-update.html', context)


@user_passes_test(lambda usr: usr.is_superuser)
@staff_member_required
def edit_tournament(request, pk=None):
    obj = get_object_or_404(Tournament, pk=pk)
    form = TournamentForm(request.POST or None, instance=obj)
    context = {
        "form": form,
    }
    if form.is_valid():
        tournament = form.save(commit=False)
        # update the slug
        slugify_instance_str(tournament, save=True)
        context['message'] = 'Tournament updated successfully'
    # if request.htmx:
    #     return render(request, "recipes/partials/forms.html", context)
    return render(request, "tournaments/create-update.html", context)


@user_passes_test(lambda usr: usr.is_superuser)
@staff_member_required
def delete_tournaments(request):
    if request.method == 'POST':
        tournament_ids = request.POST.getlist('delete-checkboxes')
        qs = Tournament.objects.filter(pk__in=tournament_ids)
        qs.delete()
    return redirect('tournaments:list')


@login_required
def get_tournament_detail(request, pk, detail_page):
    # construct the template path
    template_name = f'tournaments/partials/{detail_page}.html'
    tournament = get_object_or_404(Tournament, pk=pk)
    course = tournament.course
    user = UserProfile.objects.get(user=request.user)
    context = {'detail_template': template_name,
               "object": tournament,
               "course": course,
               "is_registered": user.is_registered(tournament.pk)}
    if detail_page == 'participants':
        # only if is staff user
        if request.user.is_staff:
            participants = tournament.participants.order_by('hcp')
            context['participants'] = participants
        else:
            return redirect('tournaments:detail', pk=tournament.pk, detail_page='overview')
    return render(request, 'tournaments/details.html', context)
