from django import forms
from .models import Atraso
from estudiantes.models import Estudiante


class AtrasoForm(forms.ModelForm):
    rut_estudiante = forms.CharField(
        label='RUT del Estudiante',
        max_length=12,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese RUT (ej: 12.345.678-9)'
        })
    )

    class Meta:
        model = Atraso
        fields = ['justificado', 'observacion']
        widgets = {
            'justificado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ingrese una observación (opcional)'
            })
        }

    def clean_rut_estudiante(self):
        rut = self.cleaned_data.get('rut_estudiante')
        if not rut:
            raise forms.ValidationError('El RUT es requerido')

        # Buscar el estudiante por RUT
        try:
            estudiante = Estudiante.objects.get(rut=rut)
            if not estudiante.activo:
                raise forms.ValidationError('El estudiante está inactivo')
            return estudiante
        except Estudiante.DoesNotExist:
            raise forms.ValidationError(
                'No se encontró un estudiante con ese RUT')
