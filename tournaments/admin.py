from django.contrib import admin

from tournaments.models import Tournament


# Register your models here.
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'tee_time', 'hcp_limit')
    search_fields = ('id', 'date', 'tee_time', 'course')
    readonly_fields = ('id', 'creation_date', 'updated_date')

admin.site.register(Tournament, TournamentAdmin)
