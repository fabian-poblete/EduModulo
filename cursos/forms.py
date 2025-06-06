from django import forms
from .models import Curso
from colegios.models import Colegio


class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['nombre', 'activo']  # se modificará dinámicamente en __init__
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and self.user.is_superuser:
            # Agregar dinámicamente el campo colegio
            self.fields['colegio'] = forms.ModelChoiceField(
                queryset=Colegio.objects.filter(activo=True),
                widget=forms.Select(attrs={'class': 'form-control'}),
                empty_label="Seleccione un colegio"
            )
            # Incluir 'colegio' en fields para validación
            self.Meta.fields.append('colegio')

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Solo asigna colegio si no es superusuario (porque los superusuarios eligen manualmente)
        if self.user and not self.user.is_superuser:
            instance.colegio = self.user.perfil.colegio
        if commit:
            instance.save()
        return instance
