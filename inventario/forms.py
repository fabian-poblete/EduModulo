from django import forms
from .models import Articulo, Categoria, Ubicacion, Estado, MovimientoArticulo, DocumentoArticulo
from colegios.models import Colegio
from django.contrib.auth.models import User


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and not self.user.is_superuser:
            if hasattr(self.user, 'perfil') and self.user.perfil.tipo_usuario == 'admin_colegio':
                self.instance.colegio = self.user.perfil.colegio


class UbicacionForm(forms.ModelForm):
    class Meta:
        model = Ubicacion
        fields = ['nombre', 'tipo', 'descripcion', 'ubicacion_padre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ubicacion_padre': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and not self.user.is_superuser:
            if hasattr(self.user, 'perfil') and self.user.perfil.tipo_usuario == 'admin_colegio':
                self.instance.colegio = self.user.perfil.colegio
                # Filter ubicacion_padre choices to only show locations from the same colegio
                self.fields['ubicacion_padre'].queryset = Ubicacion.objects.filter(
                    colegio=self.user.perfil.colegio, activo=True)


class EstadoForm(forms.ModelForm):
    class Meta:
        model = Estado
        fields = ['nombre', 'descripcion', 'icono', 'color']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'fas fa-check-circle',
                'data-bs-toggle': 'tooltip',
                'title': 'Clase de Font Awesome para el icono'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'data-bs-toggle': 'tooltip',
                'title': 'Color del estado'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and not self.user.is_superuser:
            if hasattr(self.user, 'perfil') and self.user.perfil.tipo_usuario == 'admin_colegio':
                self.instance.colegio = self.user.perfil.colegio


class ArticuloForm(forms.ModelForm):
    class Meta:
        model = Articulo
        fields = ['nombre', 'descripcion', 'categoria', 'ubicacion', 'estado',
                  'cantidad', 'stock_minimo', 'codigo_barras', 'numero_serie',
                  'fecha_adquisicion', 'valor_adquisicion', 'responsable', 'colegio']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'ubicacion': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_adquisicion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valor_adquisicion': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'responsable': forms.Select(attrs={'class': 'form-control'}),
            'colegio': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and not self.user.is_superuser:
            if hasattr(self.user, 'perfil') and self.user.perfil.tipo_usuario == 'admin_colegio':
                colegio = self.user.perfil.colegio
                self.instance.colegio = colegio

                # Filter choices to only show items from the same colegio
                self.fields['categoria'].queryset = Categoria.objects.filter(
                    colegio=colegio, activo=True)
                self.fields['ubicacion'].queryset = Ubicacion.objects.filter(
                    colegio=colegio, activo=True)
                self.fields['estado'].queryset = Estado.objects.filter(
                    colegio=colegio, activo=True)
                # Get User objects from the colegio's usuarios (Perfil objects)
                self.fields['responsable'].queryset = User.objects.filter(
                    perfil__colegio=colegio, perfil__activo=True)


class MovimientoArticuloForm(forms.ModelForm):
    class Meta:
        model = MovimientoArticulo
        fields = ['tipo', 'cantidad', 'ubicacion_origen', 'ubicacion_destino',
                  'estado_anterior', 'estado_nuevo', 'observacion']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'ubicacion_origen': forms.Select(attrs={'class': 'form-control'}),
            'ubicacion_destino': forms.Select(attrs={'class': 'form-control'}),
            'estado_anterior': forms.Select(attrs={'class': 'form-control'}),
            'estado_nuevo': forms.Select(attrs={'class': 'form-control'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.articulo = kwargs.pop('articulo', None)
        super().__init__(*args, **kwargs)

        if self.user and self.articulo:
            colegio = self.articulo.colegio
            self.instance.articulo = self.articulo
            self.instance.usuario = self.user

            # Filter choices to only show items from the same colegio
            self.fields['ubicacion_origen'].queryset = Ubicacion.objects.filter(
                colegio=colegio, activo=True)
            self.fields['ubicacion_destino'].queryset = Ubicacion.objects.filter(
                colegio=colegio, activo=True)
            self.fields['estado_anterior'].queryset = Estado.objects.filter(
                colegio=colegio, activo=True)
            self.fields['estado_nuevo'].queryset = Estado.objects.filter(
                colegio=colegio, activo=True)

            # Set initial values
            if not self.instance.pk:  # Only for new movements
                self.fields['estado_anterior'].initial = self.articulo.estado
                self.fields['ubicacion_origen'].initial = self.articulo.ubicacion


class DocumentoArticuloForm(forms.ModelForm):
    class Meta:
        model = DocumentoArticulo
        fields = ['tipo', 'nombre', 'archivo', 'descripcion']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.articulo = kwargs.pop('articulo', None)
        super().__init__(*args, **kwargs)

        if self.user and self.articulo:
            self.instance.articulo = self.articulo
            self.instance.usuario = self.user
