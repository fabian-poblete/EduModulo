from django.db import models
from estudiantes.models import Estudiante
from usuarios.models import Perfil
from colegios.models import Colegio

TIPO_JUSTIFICATIVO_CHOICES = [
    ("", "No justificado"),
    ("medico", "Médico"),
    ("enfermo", "Enfermo/a"),
    ("desregulacion", "Desregulación"),
    ("otros", "Otros"),
]


class Salida(models.Model):
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name='salidas_registradas')
    fecha = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
    tipo_justificativo = models.CharField(
        max_length=20,
        choices=TIPO_JUSTIFICATIVO_CHOICES,
        blank=True,
        null=True
    )
    otros_justificativo = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    regresado = models.BooleanField(default=False)
    fecha_regreso = models.DateField(null=True, blank=True)
    hora_regreso = models.TimeField(null=True, blank=True)
    observacion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Salida de {self.estudiante.nombre} - {self.fecha} {self.hora}"

    class Meta:
        verbose_name = 'Salida'
        verbose_name_plural = 'Salidas'
        ordering = ['-fecha', '-hora']
