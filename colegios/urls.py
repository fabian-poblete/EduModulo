from django.urls import path
from . import views

app_name = 'colegios'

urlpatterns = [
    path('', views.ColegioListView.as_view(), name='list'),
    path('crear/', views.ColegioCreateView.as_view(), name='create'),
    path('<slug:slug>/', views.ColegioDetailView.as_view(), name='detail'),
    path('<slug:slug>/editar/', views.ColegioUpdateView.as_view(), name='update'),
    path('<slug:slug>/eliminar/', views.ColegioDeleteView.as_view(), name='delete'),
]
