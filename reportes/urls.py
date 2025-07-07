from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.dashboard_analytics, name='dashboard'),
    path('api/graficos/', views.api_datos_graficos, name='api_graficos'),
    path('detallado/', views.reporte_detallado, name='detallado'),
]
