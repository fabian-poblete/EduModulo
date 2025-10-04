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
        fields = ['colegio', 'tipo_usuario',
                  'telefono', 'imprimir_automaticamente']
        widgets = {
            'colegio': forms.Select(attrs={'class': 'form-control'}),
            'tipo_usuario': forms.Select(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'imprimir_automaticamente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Evitar llamar __str__ en instance si no tiene user asociado
        safe_instance = None
        try:
            safe_instance = getattr(self, 'instance', None)
            instance_id = getattr(safe_instance, 'id', None)
            instance_user_id = getattr(
                getattr(safe_instance, 'user', None), 'id', None)
        except Exception as e:
            pass

        # Solo se permiten los tipos: admin_colegio, porteria, superusuario, administrativo
        tipo_usuario_choices = [
            ('admin_colegio', 'Administrador de Colegio'),
            ('porteria', 'Portería'),
            ('superusuario', 'Superusuario'),
            ('administrativo', 'Administrativo'),
        ]
        self.fields['tipo_usuario'].choices = tipo_usuario_choices

        # El nivel_acceso se establece automáticamente en el método clean() y save()

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
        elif tipo_usuario == 'superusuario':
            cleaned_data['nivel_acceso'] = 'avanzado'
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
            elif instance.tipo_usuario == 'superusuario':
                instance.nivel_acceso = 'avanzado'
            elif instance.tipo_usuario == 'administrativo':
                instance.nivel_acceso = 'intermedio'

        if commit:
            instance.save()
        return instance


class PerfilUpdateForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['tipo_usuario', 'colegio', 'nivel_acceso',
                  'telefono', 'imprimir_automaticamente']
        widgets = {
            'tipo_usuario': forms.Select(attrs={'class': 'form-select'}),
            'colegio': forms.Select(attrs={'class': 'form-select'}),
            'nivel_acceso': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'imprimir_automaticamente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si estamos editando (instance existe), hacer nivel_acceso no requerido
        # ya que se establece automáticamente según el tipo de usuario
        if self.instance and self.instance.pk:
            self.fields['nivel_acceso'].required = False

    def clean(self):
        cleaned_data = super().clean()
        tipo_usuario = cleaned_data.get('tipo_usuario')

        # Establecer nivel de acceso según tipo de usuario
        if tipo_usuario == 'admin_colegio':
            cleaned_data['nivel_acceso'] = 'intermedio'
        elif tipo_usuario == 'porteria':
            cleaned_data['nivel_acceso'] = 'basico'
        elif tipo_usuario == 'superusuario':
            cleaned_data['nivel_acceso'] = 'avanzado'
        elif tipo_usuario == 'administrativo':
            cleaned_data['nivel_acceso'] = 'intermedio'
        return cleaned_data
