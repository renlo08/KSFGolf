from django import forms

from accounts.models import UserProfile
from tournaments.models import Tournament, GolfCourse


class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        exclude = ['slug', 'participants']


class GolfCourseForm(forms.ModelForm):
    class Meta:
        model = GolfCourse
        fields = '__all__'
