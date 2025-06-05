from django.db import models
from django.conf import settings
import os
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.


class Backup(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    size = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default='success')
    description = models.TextField(blank=True, null=True)
    colegio = models.ForeignKey(
        'colegios.Colegio', on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Respaldo'
        verbose_name_plural = 'Respaldos'

    def __str__(self):
        return self.name

    def get_backup_path(self):
        if self.colegio:
            return os.path.join(settings.BASE_DIR, 'backups', f'colegio_{self.colegio.id}', self.name)
        return os.path.join(settings.BASE_DIR, 'backups', self.name)

    def get_db_backup_path(self):
        return os.path.join(self.get_backup_path(), 'db_backup.json')

    def get_media_backup_path(self):
        return os.path.join(self.get_backup_path(), 'media')

    def get_zip_path(self):
        return f"{self.get_backup_path()}.zip"

    @classmethod
    def get_colegio_backups(cls, colegio):
        """Obtener todos los respaldos de un colegio específico"""
        return cls.objects.filter(colegio=colegio)

    @classmethod
    def get_system_backups(cls):
        """Obtener todos los respaldos del sistema (sin colegio)"""
        return cls.objects.filter(colegio__isnull=True)
