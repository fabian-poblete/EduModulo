from django.urls import path
from . import views

app_name = 'system_backup'

urlpatterns = [
    path('', views.backup_list, name='backup_list'),
    path('create/', views.create_backup, name='create_backup'),
    path('<int:backup_id>/download/',
         views.download_backup, name='download_backup'),
    path('<int:backup_id>/restore/', views.restore_backup, name='restore_backup'),
    path('<int:backup_id>/delete/', views.delete_backup, name='delete_backup'),
]
