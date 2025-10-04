from django.db import models
from estudiantes.models import Estudiante


class Atraso(models.Model):
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name='atrasos')
    fecha = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
    justificado = models.BooleanField(default=False)
    con_certificado = models.BooleanField(default=False)
    observacion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Atraso de {self.estudiante.nombre} - {self.fecha} {self.hora}"

    class Meta:
        verbose_name = 'Atraso'
        verbose_name_plural = 'Atrasos'
        ordering = ['-fecha', '-hora']
