from django.db import models
from usuarios.models import Perfil
from colegios.models import Colegio
from django.utils import timezone


class Mensaje(models.Model):
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    remitente = models.ForeignKey(
        Perfil, on_delete=models.CASCADE, related_name='mensajes_enviados')
    destinatario = models.ForeignKey(
        Perfil, on_delete=models.CASCADE, related_name='mensajes_recibidos')
    colegio = models.ForeignKey(
        Colegio, on_delete=models.CASCADE, related_name='mensajes')
    asunto = models.CharField(max_length=200)
    contenido = models.TextField()
    prioridad = models.CharField(
        max_length=10, choices=PRIORIDAD_CHOICES, default='normal')
    leido = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_envio']
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'

    def __str__(self):
        return f"{self.asunto} - De {self.remitente} a {self.destinatario}"

    def marcar_como_leido(self):
        if not self.leido:
            self.leido = True
            self.fecha_lectura = timezone.now()
            self.save()

    @property
    def tiempo_transcurrido(self):
        """Retorna el tiempo transcurrido desde el envío del mensaje."""
        ahora = timezone.now()
        diferencia = ahora - self.fecha_envio

        if diferencia.days > 0:
            return f"Hace {diferencia.days} días"
        elif diferencia.seconds >= 3600:
            horas = diferencia.seconds // 3600
            return f"Hace {horas} horas"
        elif diferencia.seconds >= 60:
            minutos = diferencia.seconds // 60
            return f"Hace {minutos} minutos"
        else:
            return "Hace un momento"
