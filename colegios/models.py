from django.db import models
from django.utils.text import slugify


class Colegio(models.Model):
    nombre = models.CharField(max_length=200)
    codigo = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    direccion = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    sitio_web = models.URLField(blank=True)
    logo = models.ImageField(
        upload_to='colegios/logos/', null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    NOTIFICACION_CHOICES = [
        ('ninguno', 'Ninguno'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('ambos', 'Ambos'),
    ]
    notificaciones_activas = models.BooleanField(
        default=False, help_text='¿Activar notificaciones automáticas al apoderado?')
    canal_notificacion = models.CharField(
        max_length=10,
        choices=NOTIFICACION_CHOICES,
        default='ninguno',
        help_text='Canal de notificación: email, sms, ambos o ninguno.'
    )

    class Meta:
        verbose_name = 'Colegio'
        verbose_name_plural = 'Colegios'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)
