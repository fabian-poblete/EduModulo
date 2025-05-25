from django import forms
from .models import RevisionPrueba


class RevisionPruebaForm(forms.ModelForm):
    class Meta:
        model = RevisionPrueba
        fields = ['estudiante', 'curso', 'nombre_prueba',
                  'puntaje', 'retroalimentacion']
