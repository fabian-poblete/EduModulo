from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('dashboard-analytics/', views.dashboard_analytics, name='dashboard_analytics'),
    path('reporte-detallado/', views.reporte_detallado, name='reporte_detallado'),
    path('exportar-pdf/', views.exportar_reporte_pdf, name='exportar_pdf'),
    path('exportar-excel/', views.exportar_reporte_excel, name='exportar_excel'),
    path('exportar-csv/', views.exportar_reporte_csv, name='exportar_csv'),
    path('reporte-semanal/', views.reporte_semanal, name='reporte_semanal'),
    path('exportar-reporte-semanal-excel/', views.exportar_reporte_semanal_excel, name='exportar_reporte_semanal_excel'),
]
