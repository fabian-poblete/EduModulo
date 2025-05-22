from django.urls import path
from . import views

app_name = 'colegios'

urlpatterns = [
    path('', views.colegio_list, name='list'),
    path('crear/', views.colegio_create, name='create'),
    path('<slug:slug>/', views.colegio_detail, name='detail'),
    path('<slug:slug>/editar/', views.colegio_update, name='update'),
    path('<slug:colegio_slug>/sedes/crear/',
         views.sede_create, name='sede_create'),
]
