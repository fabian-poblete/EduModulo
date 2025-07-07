from django.urls import path
from . import views

app_name = 'salidas_almuerzo'

urlpatterns = [
    path('autorizados/', views.AutorizadosAlmuerzoListView.as_view(),
         name='autorizados_list'),
    path('autorizar/', views.AutorizarAlmuerzoCreateView.as_view(),
         name='autorizar_create'),
    path('autorizar/<int:pk>/',
         views.AutorizarAlmuerzoUpdateView.as_view(), name='autorizar_update'),
    path('verificar/', views.VerificarPermisoView.as_view(),
         name='verificar_permiso'),
    path('registrar_salida/', views.RegistrarSalidaView.as_view(),
         name='registrar_salida'),
    path('registrar_regreso/', views.RegistrarRegresoView.as_view(),
         name='registrar_regreso'),
    path('desautorizar/<int:pk>/',
         views.DesautorizarAlmuerzoView.as_view(), name='desautorizar'),
    path('buscar_estudiantes/', views.BuscarEstudiantesAlmuerzoView.as_view(),
         name='buscar_estudiantes'),
    path('carga-masiva/', views.CargaMasivaAutorizadosView.as_view(),
         name='carga_masiva'),
    path('descargar-ejemplo/', views.DescargarEjemploExcelView.as_view(),
         name='descargar_ejemplo'),
    path('validar_salida_ajax/', views.ValidarSalidaAjaxView.as_view(),
         name='validar_salida_ajax'),
]
