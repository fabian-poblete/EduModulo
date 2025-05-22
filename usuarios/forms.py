from django import forms
from django.contrib.auth.models import User
from .models import Perfil, Sede


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['tipo_usuario', 'colegio', 'sede', 'telefono',
                  'direccion', 'fecha_nacimiento', 'foto', 'activo']
        widgets = {
            'tipo_usuario': forms.Select(attrs={'class': 'form-select'}),
            'colegio': forms.Select(attrs={'class': 'form-select'}),
            'sede': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar las sedes basadas en el colegio seleccionado
        if 'colegio' in self.data:
            try:
                colegio_id = int(self.data.get('colegio'))
                self.fields['sede'].queryset = Sede.objects.filter(
                    colegio_id=colegio_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.colegio:
            self.fields['sede'].queryset = self.instance.colegio.sedes.all()
        else:
            self.fields['sede'].queryset = Sede.objects.none()
