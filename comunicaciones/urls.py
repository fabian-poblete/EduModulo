from django.urls import path
from . import views

app_name = 'comunicaciones'

urlpatterns = [
    path('', views.lista_mensajes, name='lista_mensajes'),
    path('enviar/', views.enviar_mensaje, name='enviar_mensaje'),
]
