from django.urls import path
from . import views

app_name = 'atrasos'

urlpatterns = [
    path('', views.atraso_list, name='list'),
    path('create/', views.atraso_create, name='create'),
    path('buscar-estudiantes/', views.buscar_estudiantes,
         name='buscar_estudiantes'),
    path('<int:pk>/delete/', views.atraso_delete, name='delete'),
]
