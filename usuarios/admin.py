from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Perfil


class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil'
    fields = ('colegio', 'tipo_usuario', 'nivel_acceso',
              'telefono', 'imprimir_automaticamente')


class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline,)
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'get_tipo_usuario', 'get_colegio', 'is_staff')
    list_filter = ('perfil__tipo_usuario', 'perfil__colegio',
                   'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name',
                     'email', 'perfil__colegio__nombre')

    def get_tipo_usuario(self, obj):
        try:
            return obj.perfil.get_tipo_usuario_display()
        except:
            return 'Sin perfil'
    get_tipo_usuario.short_description = 'Tipo de Usuario'

    def get_colegio(self, obj):
        try:
            return obj.perfil.colegio.nombre if obj.perfil.colegio else 'Sin colegio'
        except:
            return 'Sin colegio'
    get_colegio.short_description = 'Colegio'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo_usuario', 'colegio',
                    'nivel_acceso', 'imprimir_automaticamente')
    list_filter = ('tipo_usuario', 'colegio', 'nivel_acceso',
                   'imprimir_automaticamente')
    search_fields = ('user__username', 'user__first_name',
                     'user__last_name', 'colegio__nombre')
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('user', 'tipo_usuario', 'nivel_acceso')
        }),
        ('Información del Colegio', {
            'fields': ('colegio',)
        }),
        ('Configuración', {
            'fields': ('telefono', 'imprimir_automaticamente'),
            'description': 'Configuración personal del usuario'
        }),
    )
