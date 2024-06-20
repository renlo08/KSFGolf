from django.urls import path

from app import utils
from tournaments import views

app_name = 'tournaments'

urlpatterns = [
    path('', views.list_tournament, name='list'),
    path('create-tournament/', views.create_tournament, name='create'),
    path('create-course/', views.create_course, name='create-course'),
    path('delete/', views.delete_tournaments, name='delete'),
    path('<int:pk>/<str:detail_page>', views.get_tournament_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_tournament, name='edit'),
]

htmx_urlpatterns = [
    path('fetch_flights/', views.fetch_flights, name='fetch_flights'),
    path('fetch_competitors/', views.fetch_competitors, name='fetch_competitors'),
]

urlpatterns = utils.arrange_urlpatterns(urlpatterns + htmx_urlpatterns)
