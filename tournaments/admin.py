from django.contrib import admin

from tournaments.models import Tournament, Competitor


# Register your models here.
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'tee_time', 'hcp_limit')
    search_fields = ('id', 'date', 'tee_time', 'course')
    readonly_fields = ('id', 'creation_date', 'updated_date', 'display_participants_and_dates')

    def display_participants_and_dates(self, obj):
        """Create a string for the Tournament. This is required to display participant and their registration dates
        in the list view."""
        return '\n '.join(
            [f'{participant.registration_date} -- {participant.competitor}' for participant
             in obj.competitor_set.all()])

    display_participants_and_dates.short_description = 'Participants (Registration Dates)'


class CompetitorsAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'user_profile', 'registration_date')
    readonly_fields = ('tournament', 'user_profile', 'registration_date')
    search_fields = ('tournament', 'user_profile')


admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Competitor, CompetitorsAdmin)
