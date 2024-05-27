from django import forms

from tournaments.models import Tournament


class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ('date', 'tee_time', 'course', 'supervisor', 'hcp_limit')
