from django import forms
from .models import Estudiante
import re


def validar_rut(rut):
    """
    Valida el RUT chileno y retorna el RUT sin formato si es válido.
    Retorna None si el RUT es inválido.
    """
    # Eliminar puntos y guión
    rut = rut.replace('.', '').replace('-', '')

    # Verificar que el RUT tenga el formato correcto
    if not re.match(r'^[0-9]{7,8}[0-9kK]$', rut):
        return None

    # Separar número y dígito verificador
    numero = rut[:-1]
    dv = rut[-1].upper()

    # Calcular dígito verificador
    suma = 0
    multiplicador = 2

    for r in reversed(numero):
        suma += int(r) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2

    dvr = 11 - (suma % 11)

    if dvr == 11:
        dvr = '0'
    elif dvr == 10:
        dvr = 'K'
    else:
        dvr = str(dvr)

    # Verificar si el dígito verificador es correcto
    if dvr == dv:
        # Retornar RUT sin formato
        return rut
    return None


class EstudianteForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = ['nombre', 'rut', 'curso', 'email_estudiante', 'email_apoderado1',
                  'email_apoderado2', 'telefono_apoderado1', 'telefono_apoderado2', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'curso': forms.Select(attrs={'class': 'form-control'}),
            'email_estudiante': forms.EmailInput(attrs={'class': 'form-control'}),
            'email_apoderado1': forms.EmailInput(attrs={'class': 'form-control'}),
            'email_apoderado2': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono_apoderado1': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_apoderado2': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Si es una actualización, hacer el RUT no editable
        if self.instance.pk:
            self.fields['rut'].widget.attrs['readonly'] = True
            self.fields['rut'].widget.attrs['class'] = 'form-control bg-light'
            # Mostrar el RUT formateado en el campo
            self.initial['rut'] = self.instance.formatear_rut()
        else:
            # Si es un nuevo estudiante, establecer activo como True por defecto
            self.initial['activo'] = True

        # Filtrar cursos según el tipo de usuario
        if not self.user.is_superuser:
            self.fields['curso'].queryset = self.fields['curso'].queryset.filter(
                colegio=self.user.perfil.colegio
            )

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        if not rut:
            raise forms.ValidationError('El RUT es requerido')

        rut_validado = validar_rut(rut)
        if not rut_validado:
            raise forms.ValidationError('RUT inválido')

        # Verificar si el RUT ya existe (solo al crear)
        if not self.instance.pk:
            if Estudiante.objects.filter(rut=rut_validado).exists():
                raise forms.ValidationError('Este RUT ya está registrado')

        return rut_validado

    def clean_email_estudiante(self):
        email = self.cleaned_data.get('email_estudiante')
        if email:
            if Estudiante.objects.exclude(pk=self.instance.pk if self.instance.pk else None).filter(email_estudiante=email).exists():
                raise forms.ValidationError('Este email ya está registrado')
        return email

    def clean_email_apoderado1(self):
        email = self.cleaned_data.get('email_apoderado1')
        if email:
            if Estudiante.objects.exclude(pk=self.instance.pk if self.instance.pk else None).filter(email_apoderado1=email).exists():
                raise forms.ValidationError('Este email ya está registrado')
        return email

    def clean_email_apoderado2(self):
        email = self.cleaned_data.get('email_apoderado2')
        if email:
            if Estudiante.objects.exclude(pk=self.instance.pk if self.instance.pk else None).filter(email_apoderado2=email).exists():
                raise forms.ValidationError('Este email ya está registrado')
        return email
