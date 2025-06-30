from django.db import models
from colegios.models import Colegio
from estudiantes.models import Estudiante


class Notificacion(models.Model):
    TIPO_EVENTO_CHOICES = [
        ('atraso', 'Atraso'),
        ('salida', 'Salida'),
    ]
    CANAL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
    ]
    ESTADO_CHOICES = [
        ('enviada', 'Enviada'),
        ('fallida', 'Fallida'),
    ]
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    tipo_evento = models.CharField(max_length=10, choices=TIPO_EVENTO_CHOICES)
    canal = models.CharField(max_length=10, choices=CANAL_CHOICES)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_evento_display()} - {self.get_canal_display()} - {self.estudiante}"
