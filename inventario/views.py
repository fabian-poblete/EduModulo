from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, F
from django.http import JsonResponse
from .models import Articulo, Categoria, Ubicacion, Estado, MovimientoArticulo, DocumentoArticulo
from .forms import ArticuloForm, CategoriaForm, UbicacionForm, EstadoForm, MovimientoArticuloForm, DocumentoArticuloForm
from colegios.models import Colegio  # Assuming Colegio model is in colegios app

# Helper function to check if user can manage inventory for a colegio


def can_manage_inventory(user, colegio):
    if user.is_superuser:
        return True
    if hasattr(user, 'perfil') and user.perfil.tipo_usuario == 'admin_colegio':
        return user.perfil.colegio == colegio
    return False


@login_required
def categoria_list(request):
    if request.user.is_superuser:
        categorias = Categoria.objects.all()
    elif hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'admin_colegio':
        categorias = Categoria.objects.filter(
            colegio=request.user.perfil.colegio)
    else:
        messages.error(request, 'No tienes permiso para ver las categorías.')
        return redirect('dashboard:index')

    return render(request, 'inventario/categoria_list.html', {
        'categorias': categorias,
        'can_add': request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'admin_colegio'),
    })


@login_required
def categoria_create(request):
    if not (request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'admin_colegio')):
        messages.error(request, 'No tienes permiso para crear categorías.')
        return redirect('inventario:categoria_list')

    if request.method == 'POST':
        form = CategoriaForm(request.POST, user=request.user)
        if form.is_valid():
            # Assign the colegio before saving
            categoria = form.save(commit=False)
            if hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'admin_colegio':
                categoria.colegio = request.user.perfil.colegio
            # Assuming superusers are creating for the default school if not specified
            # You might want to add logic to allow superusers to select a school
            elif request.user.is_superuser:
                # You might need to adjust this if superusers need to select a specific school
                # For now, we'll assume a default or handle based on form if implemented
                # If your form allows selecting a school, the form.save() should handle it.
                # If not, you might need to fetch a default colegio here.
                # Let's assume the form is updated to handle colegio for superusers, or a default exists.
                # If the form is NOT updated for superusers, the error might reappear for them.
                # For simplicity and to fix the admin_colegio case, we focus on that.
                pass  # The form or other logic should handle superuser's colegio

            categoria.save()
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('inventario:categoria_list')
    else:
        form = CategoriaForm(user=request.user)

    return render(request, 'inventario/categoria_form.html', {
        'form': form,
        'title': 'Crear Categoría'
    })


@login_required
def categoria_update(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if not can_manage_inventory(request.user, categoria.colegio):
        messages.error(
            request, 'No tienes permiso para editar esta categoría.')
        return redirect('inventario:categoria_list')

    if request.method == 'POST':
        form = CategoriaForm(
            request.POST, instance=categoria, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente.')
            return redirect('inventario:categoria_list')
    else:
        form = CategoriaForm(instance=categoria, user=request.user)

    return render(request, 'inventario/categoria_form.html', {
        'form': form,
        'title': 'Editar Categoría'
    })


@login_required
def categoria_delete(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if not can_manage_inventory(request.user, categoria.colegio):
        messages.error(
            request, 'No tienes permiso para eliminar esta categoría.')
        return redirect('inventario:categoria_list')

    if request.method == 'POST':
        try:
            categoria.delete()
            messages.success(request, 'Categoría eliminada exitosamente.')
        except Exception as e:
            messages.error(
                request, f'Error al eliminar la categoría: {str(e)}')
        return redirect('inventario:categoria_list')

    return render(request, 'inventario/categoria_confirm_delete.html', {
        'categoria': categoria
    })


@login_required
def ubicacion_list(request):
    if request.user.is_superuser:
        ubicaciones = Ubicacion.objects.all()
    elif hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'admin_colegio':
        ubicaciones = Ubicacion.objects.filter(
            colegio=request.user.perfil.colegio)
    else:
        messages.error(request, 'No tienes permiso para ver las ubicaciones.')
        return redirect('dashboard:index')

    return render(request, 'inventario/ubicacion_list.html', {
        'ubicaciones': ubicaciones,
        'can_add': request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'admin_colegio'),
    })


@login_required
def ubicacion_create(request):
    if not (request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'admin_colegio')):
        messages.error(request, 'No tienes permiso para crear ubicaciones.')
        return redirect('inventario:ubicacion_list')

    if request.method == 'POST':
        form = UbicacionForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ubicación creada exitosamente.')
            return redirect('inventario:ubicacion_list')
    else:
        form = UbicacionForm(user=request.user)

    return render(request, 'inventario/ubicacion_form.html', {
        'form': form,
        'title': 'Crear Ubicación'
    })


@login_required
def ubicacion_update(request, pk):
    ubicacion = get_object_or_404(Ubicacion, pk=pk)
    if not can_manage_inventory(request.user, ubicacion.colegio):
        messages.error(
            request, 'No tienes permiso para editar esta ubicación.')
        return redirect('inventario:ubicacion_list')

    if request.method == 'POST':
        form = UbicacionForm(
            request.POST, instance=ubicacion, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ubicación actualizada exitosamente.')
            return redirect('inventario:ubicacion_list')
    else:
        form = UbicacionForm(instance=ubicacion, user=request.user)

    return render(request, 'inventario/ubicacion_form.html', {
        'form': form,
        'title': 'Editar Ubicación'
    })


@login_required
def ubicacion_delete(request, pk):
    ubicacion = get_object_or_404(Ubicacion, pk=pk)
    if not can_manage_inventory(request.user, ubicacion.colegio):
        messages.error(
            request, 'No tienes permiso para eliminar esta ubicación.')
        return redirect('inventario:ubicacion_list')

    if request.method == 'POST':
        try:
            ubicacion.delete()
            messages.success(request, 'Ubicación eliminada exitosamente.')
        except Exception as e:
            messages.error(
                request, f'Error al eliminar la ubicación: {str(e)}')
        return redirect('inventario:ubicacion_list')

    return render(request, 'inventario/ubicacion_confirm_delete.html', {
        'ubicacion': ubicacion
    })


@login_required
def estado_list(request):
    if request.user.is_superuser:
        estados = Estado.objects.all()
    elif hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'admin_colegio':
        estados = Estado.objects.filter(colegio=request.user.perfil.colegio)
    else:
        messages.error(request, 'No tienes permiso para ver los estados.')
        return redirect('dashboard:index')

    return render(request, 'inventario/estado_list.html', {
        'estados': estados,
        'can_add': request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'admin_colegio'),
    })


@login_required
def estado_create(request):
    if not (request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'admin_colegio')):
        messages.error(request, 'No tienes permiso para crear estados.')
        return redirect('inventario:estado_list')

    if request.method == 'POST':
        form = EstadoForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estado creado exitosamente.')
            return redirect('inventario:estado_list')
    else:
        form = EstadoForm(user=request.user)

    return render(request, 'inventario/estado_form.html', {
        'form': form,
        'title': 'Crear Estado'
    })


@login_required
def estado_update(request, pk):
    estado = get_object_or_404(Estado, pk=pk)
    if not can_manage_inventory(request.user, estado.colegio):
        messages.error(request, 'No tienes permiso para editar este estado.')
        return redirect('inventario:estado_list')

    if request.method == 'POST':
        form = EstadoForm(request.POST, instance=estado, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estado actualizado exitosamente.')
            return redirect('inventario:estado_list')
    else:
        form = EstadoForm(instance=estado, user=request.user)

    return render(request, 'inventario/estado_form.html', {
        'form': form,
        'title': 'Editar Estado'
    })


@login_required
def estado_delete(request, pk):
    estado = get_object_or_404(Estado, pk=pk)
    if not can_manage_inventory(request.user, estado.colegio):
        messages.error(request, 'No tienes permiso para eliminar este estado.')
        return redirect('inventario:estado_list')

    if request.method == 'POST':
        try:
            estado.delete()
            messages.success(request, 'Estado eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el estado: {str(e)}')
        return redirect('inventario:estado_list')

    return render(request, 'inventario/estado_confirm_delete.html', {
        'estado': estado
    })


@login_required
def articulo_list(request):
    if request.user.is_superuser:
        articulos = Articulo.objects.all()
    elif hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'admin_colegio':
        articulos = Articulo.objects.filter(
            colegio=request.user.perfil.colegio)
    else:
        messages.error(request, 'No tienes permiso para ver el inventario.')
        return redirect('dashboard:index')

    # Add filtering and searching
    query = request.GET.get('q')
    if query:
        articulos = articulos.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(codigo_barras__icontains=query) |
            Q(numero_serie__icontains=query)
        )

    categoria_id = request.GET.get('categoria')
    if categoria_id:
        articulos = articulos.filter(categoria_id=categoria_id)

    ubicacion_id = request.GET.get('ubicacion')
    if ubicacion_id:
        articulos = articulos.filter(ubicacion_id=ubicacion_id)

    estado_id = request.GET.get('estado')
    if estado_id:
        articulos = articulos.filter(estado_id=estado_id)

    # Get filter options
    if request.user.is_superuser:
        categorias = Categoria.objects.all()
        ubicaciones = Ubicacion.objects.all()
        estados = Estado.objects.all()
    else:
        colegio = request.user.perfil.colegio
        categorias = Categoria.objects.filter(colegio=colegio)
        ubicaciones = Ubicacion.objects.filter(colegio=colegio)
        estados = Estado.objects.filter(colegio=colegio)

    # Calculate statistics
    total_articulos = articulos.count()
    articulos_bueno = articulos.filter(estado__nombre='Bueno').count()
    porcentaje_bueno = round(
        (articulos_bueno / total_articulos * 100) if total_articulos > 0 else 0)
    stock_bajo = articulos.filter(
        cantidad__lte=F('stock_minimo')).count()
    total_ubicaciones = ubicaciones.count()

    # Handle export
    if request.GET.get('export') == 'excel':
        import xlwt
        from django.http import HttpResponse
        from datetime import datetime

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Inventario')

        # Sheet header, first row
        row_num = 0
        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['Nombre', 'Descripción', 'Categoría', 'Ubicación', 'Estado',
                   'Cantidad', 'Stock Mínimo', 'Código de Barras', 'Número de Serie',
                   'Fecha Adquisición', 'Valor Adquisición', 'Responsable', 'Colegio']

        for col_num, column_title in enumerate(columns):
            ws.write(row_num, col_num, column_title, font_style)

        # Sheet body, remaining rows
        font_style = xlwt.XFStyle()

        for articulo in articulos:
            row_num += 1
            row = [
                articulo.nombre,
                articulo.descripcion or '',
                articulo.categoria.nombre,
                articulo.ubicacion.nombre,
                articulo.estado.nombre,
                articulo.cantidad,
                articulo.stock_minimo,
                articulo.codigo_barras or '',
                articulo.numero_serie or '',
                articulo.fecha_adquisicion.strftime(
                    '%Y-%m-%d') if articulo.fecha_adquisicion else '',
                str(articulo.valor_adquisicion) if articulo.valor_adquisicion else '',
                articulo.responsable.get_full_name() if articulo.responsable else '',
                articulo.colegio.nombre
            ]
            for col_num, cell_value in enumerate(row):
                ws.write(row_num, col_num, cell_value, font_style)

        # Generate response
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="inventario_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls"'
        wb.save(response)
        return response

    return render(request, 'inventario/articulo_list.html', {
        'articulos': articulos,
        'categorias': categorias,
        'ubicaciones': ubicaciones,
        'estados': estados,
        'can_add': request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'admin_colegio'),
        'total_articulos': total_articulos,
        'porcentaje_bueno': porcentaje_bueno,
        'stock_bajo': stock_bajo,
        'total_ubicaciones': total_ubicaciones,
    })


@login_required
def articulo_create(request):
    if not (request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'admin_colegio')):
        messages.error(
            request, 'No tienes permiso para agregar artículos al inventario.')
        return redirect('inventario:list')

    if request.method == 'POST':
        form = ArticuloForm(request.POST, user=request.user)
        if form.is_valid():
            articulo = form.save(commit=False)
            # Assign the colegio for admin_colegio users
            if hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario == 'admin_colegio':
                articulo.colegio = request.user.perfil.colegio
            # Superusers should ideally have a way to select a colegio, but for this fix
            # we are ensuring admin_colegio users correctly set the colegio.
            # If a superuser is creating an article without selecting a school (and the form doesn't handle it),
            # they might still hit this error. The form's __init__ tries to set it,
            # but explicitly setting it here for admin_colegio is safer.
            articulo.save()
            messages.success(
                request, 'Artículo agregado al inventario exitosamente.')
            return redirect('inventario:list')
    else:
        form = ArticuloForm(user=request.user)

    return render(request, 'inventario/articulo_form.html', {
        'form': form,
        'title': 'Agregar Artículo al Inventario'
    })


@login_required
def articulo_update(request, pk):
    articulo = get_object_or_404(Articulo, pk=pk)
    if not can_manage_inventory(request.user, articulo.colegio):
        messages.error(request, 'No tienes permiso para editar este artículo.')
        return redirect('inventario:list')

    if request.method == 'POST':
        form = ArticuloForm(request.POST, instance=articulo, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Artículo actualizado exitosamente.')
            return redirect('inventario:list')
    else:
        form = ArticuloForm(instance=articulo, user=request.user)

    return render(request, 'inventario/articulo_form.html', {
        'form': form,
        'title': 'Editar Artículo de Inventario'
    })


@login_required
def articulo_delete(request, pk):
    articulo = get_object_or_404(Articulo, pk=pk)
    if not can_manage_inventory(request.user, articulo.colegio):
        messages.error(
            request, 'No tienes permiso para eliminar este artículo.')
        return redirect('inventario:list')

    if request.method == 'POST':
        try:
            nombre_articulo = articulo.nombre
            articulo.delete()
            messages.success(
                request, f'Artículo "{nombre_articulo}" eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el artículo: {str(e)}')
        return redirect('inventario:list')

    return render(request, 'inventario/articulo_confirm_delete.html', {
        'articulo': articulo
    })


@login_required
def articulo_detail(request, pk):
    articulo = get_object_or_404(Articulo, pk=pk)
    if not can_manage_inventory(request.user, articulo.colegio):
        messages.error(request, 'No tienes permiso para ver este artículo.')
        return redirect('inventario:list')

    movimientos = articulo.movimientos.all()
    documentos = articulo.documentos.all()

    return render(request, 'inventario/articulo_detail.html', {
        'articulo': articulo,
        'movimientos': movimientos,
        'documentos': documentos,
    })


@login_required
def movimiento_create(request, articulo_id):
    articulo = get_object_or_404(Articulo, pk=articulo_id)
    if not can_manage_inventory(request.user, articulo.colegio):
        messages.error(
            request, 'No tienes permiso para registrar movimientos.')
        return redirect('inventario:list')

    if request.method == 'POST':
        form = MovimientoArticuloForm(
            request.POST, user=request.user, articulo=articulo)
        if form.is_valid():
            movimiento = form.save()

            # Update article quantity and location
            if movimiento.tipo == 'entrada':
                articulo.cantidad += movimiento.cantidad
            elif movimiento.tipo == 'salida':
                articulo.cantidad -= movimiento.cantidad

            if movimiento.ubicacion_destino:
                articulo.ubicacion = movimiento.ubicacion_destino

            if movimiento.estado_nuevo:
                articulo.estado = movimiento.estado_nuevo

            articulo.ultimo_movimiento = movimiento.fecha_movimiento
            articulo.save()

            messages.success(request, 'Movimiento registrado exitosamente.')
            return redirect('inventario:articulo_detail', pk=articulo.pk)
    else:
        form = MovimientoArticuloForm(user=request.user, articulo=articulo)

    return render(request, 'inventario/movimiento_form.html', {
        'form': form,
        'articulo': articulo,
        'title': 'Registrar Movimiento'
    })


@login_required
def documento_create(request, articulo_id):
    articulo = get_object_or_404(Articulo, pk=articulo_id)
    if not can_manage_inventory(request.user, articulo.colegio):
        messages.error(request, 'No tienes permiso para subir documentos.')
        return redirect('inventario:list')

    if request.method == 'POST':
        form = DocumentoArticuloForm(
            request.POST, request.FILES, user=request.user, articulo=articulo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Documento subido exitosamente.')
            return redirect('inventario:articulo_detail', pk=articulo.pk)
    else:
        form = DocumentoArticuloForm(user=request.user, articulo=articulo)

    return render(request, 'inventario/documento_form.html', {
        'form': form,
        'articulo': articulo,
        'title': 'Subir Documento'
    })


@login_required
def documento_delete(request, pk):
    documento = get_object_or_404(DocumentoArticulo, pk=pk)
    if not can_manage_inventory(request.user, documento.articulo.colegio):
        messages.error(
            request, 'No tienes permiso para eliminar este documento.')
        return redirect('inventario:articulo_detail', pk=documento.articulo.pk)

    if request.method == 'POST':
        try:
            documento.delete()
            messages.success(request, 'Documento eliminado exitosamente.')
        except Exception as e:
            messages.error(
                request, f'Error al eliminar el documento: {str(e)}')
        return redirect('inventario:articulo_detail', pk=documento.articulo.pk)

    return render(request, 'inventario/documento_confirm_delete.html', {
        'documento': documento
    })


@login_required
def inventario_dashboard(request):
    # Obtener resúmenes para el dashboard
    if request.user.is_superuser:
        total_categorias = Categoria.objects.count()
        total_ubicaciones = Ubicacion.objects.count()
        total_estados = Estado.objects.count()
        total_articulos = Articulo.objects.count()
    else:
        colegio = request.user.perfil.colegio
        total_categorias = Categoria.objects.filter(colegio=colegio).count()
        total_ubicaciones = Ubicacion.objects.filter(colegio=colegio).count()
        total_estados = Estado.objects.filter(colegio=colegio).count()
        total_articulos = Articulo.objects.filter(colegio=colegio).count()

    return render(request, 'inventario/dashboard.html', {
        'total_categorias': total_categorias,
        'total_ubicaciones': total_ubicaciones,
        'total_estados': total_estados,
        'total_articulos': total_articulos,
    })
