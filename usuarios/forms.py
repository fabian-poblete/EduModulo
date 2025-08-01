from django import forms
from django.contrib.auth.models import User
from .models import Perfil
from colegios.models import Colegio


class UserForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico'
        }),
        required=True,
        help_text='Este será tu nombre de usuario para iniciar sesión'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        help_text='La contraseña debe tener al menos 8 caracteres'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        help_text='Confirma tu contraseña'
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        # Si estamos editando (instance existe) y no se proporcionó contraseña, no validar
        if self.instance.pk and not password and not confirm_password:
            return cleaned_data

        # Si se proporcionó una contraseña, validar que coincida
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Las contraseñas no coinciden.')

        # Si se proporcionó una contraseña, validar longitud mínima
        if password and len(password) < 8:
            raise forms.ValidationError(
                'La contraseña debe tener al menos 8 caracteres.')

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk if self.instance else None).filter(email=email).exists():
            raise forms.ValidationError(
                'Este correo electrónico ya está registrado.')
        return email


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['tipo_usuario', 'colegio']
        widgets = {
            'tipo_usuario': forms.Select(attrs={'class': 'form-select'}),
            'colegio': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Solo se permiten los tipos: admin_colegio, porteria, administrativo
        tipo_usuario_choices = [
            ('admin_colegio', 'Administrador de Colegio'),
            ('porteria', 'Portería'),
            ('administrativo', 'Administrativo'),
        ]
        self.fields['tipo_usuario'].choices = tipo_usuario_choices

    def clean(self):
        cleaned_data = super().clean()
        tipo_usuario = cleaned_data.get('tipo_usuario')
        colegio = cleaned_data.get('colegio')

        # Validar que todos los usuarios tengan un colegio asignado
        if not colegio:
            raise forms.ValidationError(
                'Debe seleccionar un colegio para este usuario.')

        # Establecer nivel de acceso según tipo de usuario
        if tipo_usuario == 'admin_colegio':
            cleaned_data['nivel_acceso'] = 'intermedio'
        elif tipo_usuario == 'porteria':
            cleaned_data['nivel_acceso'] = 'basico'
        elif tipo_usuario == 'administrativo':
            cleaned_data['nivel_acceso'] = 'intermedio'
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Asegurar que el nivel de acceso se establezca al guardar
        if not instance.nivel_acceso:
            if instance.tipo_usuario == 'admin_colegio':
                instance.nivel_acceso = 'intermedio'
            elif instance.tipo_usuario == 'porteria':
                instance.nivel_acceso = 'basico'
            elif instance.tipo_usuario == 'administrativo':
                instance.nivel_acceso = 'intermedio'

        if commit:
            instance.save()
        return instance
