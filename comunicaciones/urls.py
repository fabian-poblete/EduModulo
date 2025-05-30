from django.urls import path
from . import views

app_name = 'comunicaciones'

urlpatterns = [
    path('', views.lista_mensajes, name='lista_mensajes'),
    path('enviar/', views.enviar_mensaje, name='enviar_mensaje'),
    path('ver/<int:pk>/', views.ver_mensaje, name='ver_mensaje'),
    path('eliminar/<int:pk>/', views.eliminar_mensaje, name='eliminar_mensaje'),
    path('responder/<int:pk>/', views.responder_mensaje, name='responder_mensaje'),
]
