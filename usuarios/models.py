from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from colegios.models import Colegio


class Perfil(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('admin_colegio', 'Administrador de Colegio'),
        ('porteria', 'Portería'),
        ('superusuario', 'Superusuario'),
        ('administrativo', 'Administrativo'),
    ]

    NIVEL_ACCESO_CHOICES = [
        ('basico', 'Básico'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
        ('admin', 'Administrador'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    colegio = models.ForeignKey(
        'colegios.Colegio', on_delete=models.CASCADE, null=True, blank=True)
    tipo_usuario = models.CharField(
        max_length=20, choices=TIPO_USUARIO_CHOICES, default='porteria')
    nivel_acceso = models.CharField(
        max_length=20, choices=NIVEL_ACCESO_CHOICES, default='basico')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    imprimir_automaticamente = models.BooleanField(
        default=True,
        verbose_name="Imprimir automáticamente",
        help_text="Si está marcado, se intentará imprimir automáticamente desde la web"
    )

    @property
    def debe_imprimir_automaticamente(self):
        """
        Los usuarios de portería SIEMPRE imprimen automáticamente
        Otros usuarios siguen su configuración personal
        """
        if self.tipo_usuario == 'porteria':
            return True
        return self.imprimir_automaticamente

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
    def es_admin_colegio(self):
        return self.tipo_usuario == 'admin_colegio'

    @property
    def puede_administrar_colegio(self):
        return self.es_admin_colegio

    @property
    def es_equipo_soporte(self):
        """Determina si el usuario es parte del equipo de soporte"""
        return self.tipo_usuario in ['admin_colegio', 'superusuario', 'administrativo']


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
