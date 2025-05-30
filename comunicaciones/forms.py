from django import forms
from .models import Mensaje
from usuarios.models import Perfil


class MensajeForm(forms.ModelForm):
    class Meta:
        model = Mensaje
        fields = ['destinatario', 'asunto', 'contenido', 'prioridad']
        widgets = {
            'destinatario': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Seleccione el destinatario'
            }),
            'asunto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Asunto del mensaje'
            }),
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Escriba su mensaje aquí...'
            }),
            'prioridad': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filtrar destinatarios según el colegio del usuario
        if self.user and not self.user.is_superuser:
            self.fields['destinatario'].queryset = Perfil.objects.filter(
                colegio=self.user.perfil.colegio
            ).exclude(id=self.user.perfil.id)
        else:
            self.fields['destinatario'].queryset = Perfil.objects.all().exclude(
                id=self.user.perfil.id if self.user else None
            )
