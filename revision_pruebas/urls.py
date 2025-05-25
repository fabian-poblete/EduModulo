from django.urls import path
from . import views

app_name = 'revision_pruebas'

urlpatterns = [
    path('', views.lista_revisiones, name='lista_revisiones'),
    path('registrar/', views.registrar_revision, name='registrar_revision'),
]
