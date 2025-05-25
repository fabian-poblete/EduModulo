from django.db import models
from estudiantes.models import Estudiante
from usuarios.models import Perfil
from cursos.models import Curso
from colegios.models import Colegio


class RevisionPrueba(models.Model):
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name='revisiones')
    profesor = models.ForeignKey(Perfil, on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='revisiones_realizadas')
    curso = models.ForeignKey(
        Curso, on_delete=models.CASCADE, related_name='revisiones')
    colegio = models.ForeignKey(
        Colegio, on_delete=models.CASCADE, related_name='revisiones')
    nombre_prueba = models.CharField(max_length=255)
    puntaje = models.DecimalField(max_digits=5, decimal_places=2)
    retroalimentacion = models.TextField(blank=True)
    fecha_revision = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_revision']

    def __str__(self):
        return f"{self.nombre_prueba} - {self.estudiante}"
