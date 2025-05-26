from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.usuario_list, name='list'),
    path('crear/', views.usuario_create, name='create'),
    path('crear/<int:colegio_id>/', views.usuario_create,
         name='create_with_colegio'),
    path('<int:pk>/', views.usuario_detail, name='detail'),
    path('<int:pk>/editar/', views.usuario_update, name='update'),
    path('<int:pk>/eliminar/', views.usuario_delete, name='delete'),
    path('perfil/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
]
