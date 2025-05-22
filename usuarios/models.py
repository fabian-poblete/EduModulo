from django.db import models
from django.contrib.auth.models import User
from colegios.models import Colegio, Sede


class Perfil(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('admin', 'Administrador'),
        ('director', 'Director'),
        ('profesor', 'Profesor'),
        ('estudiante', 'Estudiante'),
        ('acudiente', 'Acudiente'),
    ]

    usuario = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='perfil')
    tipo_usuario = models.CharField(
        max_length=20, choices=TIPO_USUARIO_CHOICES)
    colegio = models.ForeignKey(
        Colegio, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    sede = models.ForeignKey(
        Sede, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    foto = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
        ordering = ['usuario__username']

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.get_tipo_usuario_display()}"

    def get_tipo_usuario_display(self):
        return dict(self.TIPO_USUARIO_CHOICES).get(self.tipo_usuario, self.tipo_usuario)
