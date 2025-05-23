from django import forms
from .models import Curso
from colegios.models import Colegio


class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['nombre', 'colegio', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'colegio': forms.Select(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Si es admin de colegio, forzar el colegio y ocultar el campo
        if self.user and not self.user.is_superuser:
            self.instance.colegio = self.user.perfil.colegio
            self.fields['colegio'].widget = forms.HiddenInput()
            self.fields['colegio'].initial = self.user.perfil.colegio
        else:
            # Si es superusuario, mostrar todos los colegios activos
            self.fields['colegio'].queryset = Colegio.objects.filter(
                activo=True)
            self.fields['colegio'].empty_label = "Seleccione un colegio"
