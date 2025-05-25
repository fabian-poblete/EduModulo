from django import forms
from .models import SalidaAnticipada


class SalidaAnticipadaForm(forms.ModelForm):
    class Meta:
        model = SalidaAnticipada
        fields = ['estudiante', 'motivo', 'fecha_salida']
        widgets = {
            'fecha_salida': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }
