from django.db import models
from colegios.models import Colegio


class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    colegio = models.ForeignKey(
        Colegio, on_delete=models.CASCADE, related_name='cursos')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['colegio', 'nombre']
        unique_together = ['nombre', 'colegio']

    def __str__(self):
        return f"{self.nombre} "
