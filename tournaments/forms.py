from django import forms

from tournaments.models import Tournament, GolfCourse


class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = '__all__'


class GolfCourseForm(forms.ModelForm):
    class Meta:
        model = GolfCourse
        fields = '__all__'
