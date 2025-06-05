from django.db import models
from django.conf import settings
import os

# Create your models here.


class Backup(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    size = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default='success')
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Respaldo'
        verbose_name_plural = 'Respaldos'

    def __str__(self):
        return self.name

    def get_backup_path(self):
        return os.path.join(settings.BASE_DIR, 'backups', self.name)

    def get_db_backup_path(self):
        return os.path.join(self.get_backup_path(), 'db_backup.json')

    def get_media_backup_path(self):
        return os.path.join(self.get_backup_path(), 'media')

    def get_zip_path(self):
        return f"{self.get_backup_path()}.zip"
