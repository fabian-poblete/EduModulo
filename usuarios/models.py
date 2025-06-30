from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from colegios.models import Colegio


class Perfil(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('estudiante', 'Estudiante'),
        ('profesor', 'Profesor'),
        ('apoderado', 'Apoderado'),
        ('admin_colegio', 'Administrador de Colegio'),
        ('soporte', 'Equipo de Soporte'),
    ]

    NIVEL_ACCESO_CHOICES = [
        ('basico', 'Básico'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='perfil')
    tipo_usuario = models.CharField(
        max_length=20, choices=TIPO_USUARIO_CHOICES)
    nivel_acceso = models.CharField(
        max_length=20, choices=NIVEL_ACCESO_CHOICES, default='basico')
    colegio = models.ForeignKey(
        Colegio, on_delete=models.CASCADE, null=True, blank=True, related_name='usuarios')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_tipo_usuario_display()}"

    def get_tipo_usuario_display(self):
        return dict(self.TIPO_USUARIO_CHOICES).get(self.tipo_usuario, self.tipo_usuario)

    def get_iniciales(self):
        """Retorna las iniciales del nombre completo del usuario."""
        nombre_completo = self.user.get_full_name() or self.user.username
        palabras = nombre_completo.split()
        if len(palabras) >= 2:
            return f"{palabras[0][0]}{palabras[-1][0]}".upper()
        return nombre_completo[0].upper()

    @property
    def es_equipo_soporte(self):
        return self.tipo_usuario == 'soporte'

    @property
    def es_admin_colegio(self):
        return self.tipo_usuario == 'admin_colegio'

    @property
    def puede_administrar_colegio(self):
        return self.es_equipo_soporte or self.es_admin_colegio


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """
    Señal para crear automáticamente un perfil cuando se crea un usuario.
    """
    if created:
        Perfil.objects.create(user=instance)


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """
    Señal para guardar el perfil cuando se actualiza el usuario.
    """
    try:
        instance.perfil.save()
    except Perfil.DoesNotExist:
        Perfil.objects.create(user=instance)
