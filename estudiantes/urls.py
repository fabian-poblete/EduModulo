from django.urls import path
from . import views

app_name = 'estudiantes'

urlpatterns = [
    path('', views.estudiante_list, name='list'),
    path('create/', views.estudiante_create, name='create'),
    path('create/<int:colegio_id>/', views.estudiante_create,
         name='create_with_colegio'),
    path('<int:pk>/update/', views.estudiante_update, name='update'),
    path('<int:pk>/delete/', views.estudiante_delete, name='delete'),
    path('carga-masiva/', views.carga_masiva, name='carga_masiva'),
    path('edicion-masiva/', views.edicion_masiva, name='edicion_masiva'),
    path('descargar-estudiantes/', views.descargar_estudiantes,
         name='descargar_estudiantes'),
    path('descargar-formato/', views.descargar_formato, name='descargar_formato'),
]
