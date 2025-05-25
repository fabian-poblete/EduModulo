from django.urls import path
from . import views

app_name = 'salidas'

urlpatterns = [
    path('', views.lista_salidas, name='lista_salidas'),
    path('registrar/', views.registrar_salida, name='registrar_salida'),
    path('<int:pk>/', views.detalle_salida, name='detalle_salida'),
]
