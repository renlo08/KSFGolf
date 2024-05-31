from django.urls import path

from tournaments import views

app_name = 'tournaments'

urlpatterns = [
    path('', views.list_tournament, name='list'),
    path('create-tournament/', views.create_tournament, name='create'),
    path('create-course/', views.create_course, name='create-course'),
    path('delete/', views.delete_tournaments, name='delete'),
    path('<str:slug>/edit/', views.edit_tournament, name='edit'),
    path('<str:slug>/', views.tournament_details_view, name='details'),
]
