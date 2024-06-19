from django.contrib import admin

from tournaments.models import Tournament, Competitor


# Register your models here.
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'tee_time', 'hcp_limit')
    search_fields = ('id', 'date', 'tee_time', 'course')
    readonly_fields = ('id', 'creation_date', 'updated_date')


class CompetitorsAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'competitor', 'registration_date')
    readonly_fields = ('tournament', 'competitor', 'registration_date')


admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Competitor, CompetitorsAdmin)
