from django.db import models
from estudiantes.models import Estudiante
from django.contrib.auth.models import User

# Create your models here.


class AutorizacionAlmuerzo(models.Model):
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name='autorizaciones_almuerzo')
    autorizado = models.BooleanField(default=False)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.estudiante} - {'Autorizado' if self.autorizado else 'No autorizado'}"


class RegistroSalidaAlmuerzo(models.Model):
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name='registros_salida_almuerzo')
    fecha = models.DateField(auto_now_add=True)
    hora_salida = models.TimeField(null=True, blank=True)
    hora_regreso = models.TimeField(null=True, blank=True)
    autorizado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='registros_autorizados_almuerzo')
    observaciones = models.TextField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.estudiante} - {self.fecha}"
