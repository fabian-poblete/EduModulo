from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class ReporteConfiguracion(models.Model):
    """Configuración de reportes personalizados"""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    tipo_reporte = models.CharField(
        max_length=20,
        choices=[
            ('atrasos', 'Atrasos'),
            ('salidas', 'Salidas'),
            ('combinado', 'Combinado'),
        ]
    )
    filtros = models.JSONField(default=dict)
    configuracion_graficos = models.JSONField(default=dict)
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_reporte_display()}"

    class Meta:
        verbose_name = 'Configuración de Reporte'
        verbose_name_plural = 'Configuraciones de Reportes'


class CacheAnalytics(models.Model):
    """Cache para datos analíticos para mejorar rendimiento"""
    tipo_datos = models.CharField(max_length=50)
    filtros_hash = models.CharField(max_length=64, unique=True)
    datos = models.JSONField()
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()

    def __str__(self):
        return f"{self.tipo_datos} - {self.fecha_generacion}"

    class Meta:
        verbose_name = 'Cache de Analytics'
        verbose_name_plural = 'Cache de Analytics'
        indexes = [
            models.Index(fields=['tipo_datos', 'fecha_expiracion']),
        ]

    def is_expired(self):
        return timezone.now() > self.fecha_expiracion
