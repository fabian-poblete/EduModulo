from django.urls import path
from . import views

app_name = 'cursos'

urlpatterns = [
    path('', views.curso_list, name='list'),
    path('crear/', views.curso_create, name='create'),
    path('crear/<int:colegio_id>/', views.curso_create,
         name='create_with_colegio'),
    path('<int:pk>/editar/', views.curso_update, name='update'),
    path('<int:pk>/eliminar/', views.curso_delete, name='delete'),
]
