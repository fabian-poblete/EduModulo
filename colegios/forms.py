from django import forms
from .models import Colegio


class ColegioForm(forms.ModelForm):
    class Meta:
        model = Colegio
        fields = [
            'nombre',
            'codigo',
            'direccion',
            'ciudad',
            'telefono',
            'email',
            'sitio_web',
            'logo',
            'activo',
            'notificaciones_activas',
            'canal_notificacion'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'sitio_web': forms.URLInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notificaciones_activas': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'canal_notificacion': forms.Select(attrs={'class': 'form-control'})
        }
