from django.urls import path

from tournaments import views

app_name = 'tournaments'

urlpatterns = [
    path('', views.list_tournament, name='list'),
    path('create-tournament/', views.create_tournament, name='create-tournament'),
    path('create-course/', views.create_course, name='create-course'),
    path('<str:slug>/edit/', views.edit_tournament, name='edit-tournament'),
]
