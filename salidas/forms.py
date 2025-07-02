from django import forms
from .models import Salida
from estudiantes.models import Estudiante
from estudiantes.forms import validar_rut


class SalidaForm(forms.ModelForm):
    rut_estudiante = forms.CharField(
        label='RUT del Estudiante',
        max_length=12,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese RUT (ej: 123456789)'
        })
    )
    tipo_justificativo = forms.ChoiceField(
        label='Tipo de Justificativo',
        choices=[
            ("", "No justificado"),
            ("medico", "Médico"),
            ("enfermo", "Enfermo/a"),
            ("desregulacion", "Desregulación"),
            ("otros", "Otros"),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )
    otros_justificativo = forms.CharField(
        label='Especifique otro justificativo',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'id_otros_justificativo'
        })
    )

    class Meta:
        model = Salida
        fields = ['tipo_justificativo', 'otros_justificativo', 'observacion']
        widgets = {
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

        # Validar y limpiar el RUT
        rut_validado = validar_rut(rut)
        if not rut_validado:
            raise forms.ValidationError('RUT inválido')

        # Buscar el estudiante por RUT
        try:
            estudiante = Estudiante.objects.get(rut=rut_validado)
            if not estudiante.activo:
                raise forms.ValidationError('El estudiante está inactivo')
            return estudiante
        except Estudiante.DoesNotExist:
            raise forms.ValidationError(
                'No se encontró un estudiante con ese RUT')
