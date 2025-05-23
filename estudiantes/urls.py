from django.urls import path
from . import views

app_name = 'estudiantes'

urlpatterns = [
    path('', views.estudiante_list, name='list'),
    path('create/', views.estudiante_create, name='create'),
    path('<int:pk>/update/', views.estudiante_update, name='update'),
    path('<int:pk>/delete/', views.estudiante_delete, name='delete'),
    path('carga-masiva/', views.carga_masiva, name='carga_masiva'),
    path('descargar-formato/', views.descargar_formato, name='descargar_formato'),
]
