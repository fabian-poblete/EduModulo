from django.urls import path
from . import views

app_name = 'cursos'

urlpatterns = [
    path('', views.curso_list, name='list'),
    path('crear/', views.curso_create, name='create'),
    path('<int:pk>/editar/', views.curso_update, name='update'),
    path('<int:pk>/eliminar/', views.curso_delete, name='delete'),
]
