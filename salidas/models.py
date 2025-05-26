from django.db import models
from estudiantes.models import Estudiante
from usuarios.models import Perfil
from colegios.models import Colegio


class SalidaAnticipada(models.Model):
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name='salidas_anticipadas')
    autorizado_por = models.ForeignKey(
        Perfil, on_delete=models.SET_NULL, null=True, blank=True, related_name='salidas_autorizadas')
    colegio = models.ForeignKey(
        Colegio, on_delete=models.CASCADE, related_name='salidas')
    motivo = models.CharField(max_length=255)
    fecha_salida = models.DateTimeField()
    notificado = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_salida']

    def __str__(self):
        return f"{self.estudiante} - {self.fecha_salida}"


class Salida(models.Model):
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name='salidas_registradas')
    fecha = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
    justificado = models.BooleanField(default=False)
    observacion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Salida de {self.estudiante.nombre} - {self.fecha} {self.hora}"

    class Meta:
        verbose_name = 'Salida'
        verbose_name_plural = 'Salidas'
        ordering = ['-fecha', '-hora']
