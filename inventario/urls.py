from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

app_name = 'inventario'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.inventario_dashboard, name='dashboard'),

    # Categorías
    path('categorias/', views.categoria_list, name='categoria_list'),
    path('categorias/agregar/', views.categoria_create, name='categoria_create'),
    path('categorias/<int:pk>/editar/',
         views.categoria_update, name='categoria_update'),
    path('categorias/<int:pk>/eliminar/',
         views.categoria_delete, name='categoria_delete'),

    # Ubicaciones
    path('ubicaciones/', views.ubicacion_list, name='ubicacion_list'),
    path('ubicaciones/agregar/', views.ubicacion_create, name='ubicacion_create'),
    path('ubicaciones/<int:pk>/editar/',
         views.ubicacion_update, name='ubicacion_update'),
    path('ubicaciones/<int:pk>/eliminar/',
         views.ubicacion_delete, name='ubicacion_delete'),

    # Estados
    path('estados/', views.estado_list, name='estado_list'),
    path('estados/agregar/', views.estado_create, name='estado_create'),
    path('estados/<int:pk>/editar/', views.estado_update, name='estado_update'),
    path('estados/<int:pk>/eliminar/', views.estado_delete, name='estado_delete'),

    # Artículos
    path('', views.articulo_list, name='list'),
    path('agregar/', views.articulo_create, name='add'),
    path('<int:pk>/', views.articulo_detail, name='detail'),
    path('<int:pk>/editar/', views.articulo_update, name='edit'),
    path('<int:pk>/eliminar/', views.articulo_delete, name='delete'),

    # Movimientos
    path('<int:articulo_id>/movimiento/agregar/',
         views.movimiento_create, name='movimiento_create'),

    # Documentos
    path('<int:articulo_id>/documento/agregar/',
         views.documento_create, name='documento_create'),
    path('documento/<int:pk>/eliminar/',
         views.documento_delete, name='documento_delete'),
]


@login_required
def inventario_dashboard(request):
    return render(request, 'inventario/dashboard.html')
