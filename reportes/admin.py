from django.contrib import admin
from .models import ReporteConfiguracion, CacheAnalytics


@admin.register(ReporteConfiguracion)
class ReporteConfiguracionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_reporte',
                    'creado_por', 'fecha_creacion', 'activo']
    list_filter = ['tipo_reporte', 'activo', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion', 'creado_por__username']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'tipo_reporte', 'activo')
        }),
        ('Configuración', {
            'fields': ('filtros', 'configuracion_graficos')
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CacheAnalytics)
class CacheAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['tipo_datos', 'fecha_generacion',
                    'fecha_expiracion', 'is_expired_display']
    list_filter = ['tipo_datos', 'fecha_generacion', 'fecha_expiracion']
    search_fields = ['tipo_datos', 'filtros_hash']
    readonly_fields = ['fecha_generacion']

    def is_expired_display(self, obj):
        return obj.is_expired()
    is_expired_display.boolean = True
    is_expired_display.short_description = 'Expirado'

    fieldsets = (
        ('Información del Cache', {
            'fields': ('tipo_datos', 'filtros_hash', 'datos')
        }),
        ('Fechas', {
            'fields': ('fecha_generacion', 'fecha_expiracion')
        }),
    )
