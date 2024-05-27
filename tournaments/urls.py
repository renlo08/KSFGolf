from django.urls import path

from tournaments import views

app_name = 'tournaments'

urlpatterns = [
    path('', views.tournament_list, name='list'),
    path('create/', views.tournament_create, name='create'),
]