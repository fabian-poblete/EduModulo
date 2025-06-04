from django.db import models
from django.contrib.auth.models import User
from colegios.models import Colegio


class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    colegio = models.ForeignKey(
        Colegio, on_delete=models.CASCADE, related_name='categorias')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']
        unique_together = ['nombre', 'colegio']

    def __str__(self):
        return f"{self.nombre}"


class Ubicacion(models.Model):
    TIPO_CHOICES = [
        ('edificio', 'Edificio'),
        ('sala', 'Sala'),
        ('oficina', 'Oficina'),
        ('bodega', 'Bodega'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.TextField(blank=True, null=True)
    ubicacion_padre = models.ForeignKey('self', on_delete=models.CASCADE,
                                        related_name='sububicaciones',
                                        null=True, blank=True)
    colegio = models.ForeignKey(
        Colegio, on_delete=models.CASCADE, related_name='ubicaciones')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ubicación'
        verbose_name_plural = 'Ubicaciones'
        ordering = ['tipo', 'nombre']
        unique_together = ['nombre', 'colegio', 'tipo']

    def __str__(self):
        if self.ubicacion_padre:
            return f"{self.nombre} ({self.get_tipo_display()}) - {self.ubicacion_padre.nombre}"
        return f"{self.nombre} ({self.get_tipo_display()})"


class Estado(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)
    icono = models.CharField(max_length=50, default='fas fa-circle',
                             help_text='Clase de Font Awesome para el icono (ej: fas fa-check-circle)')
    color = models.CharField(max_length=7, default='#6c757d',
                             help_text='Color en formato hexadecimal (ej: #28a745 para verde)')
    colegio = models.ForeignKey(
        Colegio, on_delete=models.CASCADE, related_name='estados')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        ordering = ['nombre']
        unique_together = ['nombre', 'colegio']

    def __str__(self):
        return f"{self.nombre} "


class Articulo(models.Model):
    colegio = models.ForeignKey(
        Colegio, on_delete=models.CASCADE, related_name='inventario')
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name='articulos')
    ubicacion = models.ForeignKey(
        Ubicacion, on_delete=models.PROTECT, related_name='articulos')
    estado = models.ForeignKey(
        Estado, on_delete=models.PROTECT, related_name='articulos')
    cantidad = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=0)
    codigo_barras = models.CharField(
        max_length=50, blank=True, null=True, unique=True)
    numero_serie = models.CharField(max_length=100, blank=True, null=True)
    fecha_adquisicion = models.DateField(null=True, blank=True)
    valor_adquisicion = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_adicion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    ultimo_movimiento = models.DateTimeField(null=True, blank=True)
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='articulos_responsables')
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Artículo de Inventario'
        verbose_name_plural = 'Artículos de Inventario'
        ordering = ['colegio', 'categoria', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.cantidad}) "

    def necesita_reposicion(self):
        return self.cantidad <= self.stock_minimo


class MovimientoArticulo(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
        ('traslado', 'Traslado'),
    ]

    articulo = models.ForeignKey(
        Articulo, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    cantidad = models.IntegerField()  # Positive for entrada, negative for salida
    ubicacion_origen = models.ForeignKey(Ubicacion, on_delete=models.PROTECT,
                                         related_name='movimientos_origen', null=True, blank=True)
    ubicacion_destino = models.ForeignKey(Ubicacion, on_delete=models.PROTECT,
                                          related_name='movimientos_destino', null=True, blank=True)
    estado_anterior = models.ForeignKey(Estado, on_delete=models.PROTECT,
                                        related_name='movimientos_estado_anterior', null=True, blank=True)
    estado_nuevo = models.ForeignKey(Estado, on_delete=models.PROTECT,
                                     related_name='movimientos_estado_nuevo', null=True, blank=True)
    observacion = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='movimientos_realizados')
    fecha_movimiento = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimiento de Artículo'
        verbose_name_plural = 'Movimientos de Artículos'
        ordering = ['-fecha_movimiento']

    def __str__(self):
        return f"{self.get_tipo_display()} de {self.articulo.nombre} - {self.fecha_movimiento}"


class DocumentoArticulo(models.Model):
    TIPO_CHOICES = [
        ('imagen', 'Imagen'),
        ('factura', 'Factura'),
        ('boleta', 'Boleta'),
        ('manual', 'Manual'),
        ('otro', 'Otro'),
    ]

    articulo = models.ForeignKey(
        Articulo, on_delete=models.CASCADE, related_name='documentos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    nombre = models.CharField(max_length=255)
    archivo = models.FileField(upload_to='documentos_articulos/')
    descripcion = models.TextField(blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='documentos_subidos')

    class Meta:
        verbose_name = 'Documento de Artículo'
        verbose_name_plural = 'Documentos de Artículos'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.nombre} - {self.articulo.nombre}"
