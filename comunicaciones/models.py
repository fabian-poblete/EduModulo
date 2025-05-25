from django.db import models
from usuarios.models import Perfil
from colegios.models import Colegio


class Mensaje(models.Model):
    remitente = models.ForeignKey(
        Perfil, on_delete=models.CASCADE, related_name='mensajes_enviados')
    destinatario = models.ForeignKey(
        Perfil, on_delete=models.CASCADE, related_name='mensajes_recibidos')
    colegio = models.ForeignKey(
        Colegio, on_delete=models.CASCADE, related_name='mensajes')
    contenido = models.TextField()
    leido = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_envio']

    def __str__(self):
        return f"De {self.remitente} a {self.destinatario} ({self.fecha_envio})"
