from django.urls import path
from . import views

app_name = 'salidas'

urlpatterns = [
    path('', views.lista_salidas, name='list'),
    path('registrar/', views.registrar_salida, name='registrar_salida'),
    path('buscar-estudiantes/', views.buscar_estudiantes_salida,
         name='buscar_estudiantes'),
    path('<int:pk>/eliminar/', views.salida_delete, name='delete'),
    path('<int:pk>/marcar-regreso/', views.marcar_regreso, name='marcar_regreso'),
    path('imprimir/<int:salida_id>/', views.imprimir_salida, name='imprimir'),
    path('reportes/', views.reportes_salida, name='reportes_salida'),
]
