from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.usuario_list, name='list'),
    path('crear/', views.usuario_create, name='create'),
    path('<int:pk>/', views.usuario_detail, name='detail'),
    path('<int:pk>/editar/', views.usuario_update, name='update'),
    path('perfil/', views.profile, name='profile'),
]
