from django.db import models
from django.core.validators import MinValueValidator
from cursos.models import Curso


class Estudiante(models.Model):
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=9, unique=True)
    curso = models.ForeignKey(
        Curso, on_delete=models.CASCADE, related_name='estudiantes')
    email_estudiante = models.EmailField(null=True, blank=True)
    email_apoderado1 = models.EmailField(null=True, blank=True)
    email_apoderado2 = models.EmailField(null=True, blank=True)
    telefono_apoderado1 = models.CharField(
        max_length=20, null=True, blank=True)
    telefono_apoderado2 = models.CharField(
        max_length=20, null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.formatear_rut()})"

    class Meta:
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
        ordering = ['nombre']

    def get_colegio(self):
        return self.curso.colegio

    def formatear_rut(self):
        """Formatea el RUT para mostrarlo con puntos y guión"""
        if len(self.rut) < 2:
            return self.rut
        try:
            numero = self.rut[:-1]
            dv = self.rut[-1].upper()
            if numero.isdigit():
                numero_formateado = f"{int(numero):,}".replace(',', '.')
                return f"{numero_formateado}-{dv}"
            else:
                return self.rut
        except (ValueError, IndexError):
            return self.rut
