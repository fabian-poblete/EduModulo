from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.dashboard_analytics, name='dashboard'),
    path('api/graficos/', views.api_datos_graficos, name='api_graficos'),
    path('detallado/', views.reporte_detallado, name='detallado'),
    path('exportar/pdf/', views.exportar_reporte_pdf, name='exportar_pdf'),
    path('exportar/excel/', views.exportar_reporte_excel, name='exportar_excel'),
    path('exportar/csv/', views.exportar_reporte_csv, name='exportar_csv'),
]
