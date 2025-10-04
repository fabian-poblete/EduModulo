from django.contrib import admin
from .models import Atraso


@admin.register(Atraso)
class AtrasoAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'fecha', 'hora',
                    'tipo_atraso', 'observacion')
    list_filter = ('fecha', 'justificado', 'con_certificado')
    search_fields = ('estudiante__nombre', 'estudiante__rut')
    ordering = ('-fecha', '-hora')

    def tipo_atraso(self, obj):
        """Mostrar el tipo de atraso de forma legible"""
        if obj.con_certificado:
            return "Certificado"
        elif obj.justificado:
            return "Justificado"
        else:
            return "No justificado"
    tipo_atraso.short_description = "Tipo de Atraso"
