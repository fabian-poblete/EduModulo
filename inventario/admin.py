from django.contrib import admin
from .models import Categoria, Ubicacion, Estado, Articulo, MovimientoArticulo, DocumentoArticulo

# Register your models here.
admin.site.register(Categoria)
admin.site.register(Ubicacion)
admin.site.register(Estado)
admin.site.register(Articulo)
admin.site.register(MovimientoArticulo)
admin.site.register(DocumentoArticulo)
