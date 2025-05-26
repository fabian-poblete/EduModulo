from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Salida
from .forms import SalidaForm
from usuarios.models import Perfil
from estudiantes.models import Estudiante
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.db.models import Q
from datetime import datetime, date


def puede_ver_salidas(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.perfil.tipo_usuario in ['admin_colegio', 'profesor', 'apoderado']


@login_required
@user_passes_test(puede_ver_salidas)
def lista_salidas(request):
    # Filter salidas based on user type (similar to atrasos_list)
    if request.user.is_superuser:
        salidas = Salida.objects.all()
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        salidas = Salida.objects.filter(
            estudiante__curso__colegio=request.user.perfil.colegio)
    elif request.user.perfil.tipo_usuario == 'profesor':
        # Assuming teachers can only see salidas from their colegio's students
        salidas = Salida.objects.filter(
            estudiante__curso__colegio=request.user.perfil.colegio)
    else:
        messages.error(request, 'No tienes permiso para ver esta página.')
        return redirect('dashboard:index')

    # Filtering logic (similar to atrasos_list)
    fecha_filtro = request.GET.get('fecha')
    if fecha_filtro:
        try:
            fecha = datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
            salidas = salidas.filter(fecha=fecha)
        except ValueError:
            messages.error(request, 'Formato de fecha inválido')

    busqueda = request.GET.get('q')
    if busqueda:
        salidas = salidas.filter(
            Q(estudiante__nombre__icontains=busqueda) |
            Q(estudiante__rut__icontains=busqueda)
        )

    return render(request, 'salidas/lista_salidas.html', {
        'salidas': salidas,
        'fecha_filtro': fecha_filtro,
        'busqueda': busqueda
    })


@login_required
@user_passes_test(puede_ver_salidas)
def registrar_salida(request):
    if request.method == 'POST':
        form = SalidaForm(request.POST)
        if form.is_valid():
            try:
                salida = form.save(commit=False)
                salida.estudiante = form.cleaned_data['rut_estudiante']
                # Fecha and Hora are auto_now_add=True in the model, so they'll be set automatically
                salida.save()
                messages.success(request, 'Salida registrada exitosamente.')
                # Assuming 'list' is the URL name for the list view
                return redirect('salidas:list')
            except Exception as e:
                messages.error(
                    request, f'Error al registrar la salida: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        form = SalidaForm()

    return render(request, 'salidas/registrar_salida.html', {
        'form': form,
        'title': 'Registrar Salida'
    })


@login_required
@user_passes_test(puede_ver_salidas)
def detalle_salida(request, pk):
    salida = get_object_or_404(Salida, pk=pk)
    perfil = request.user.perfil
    # Permitir ver solo si es admin_colegio, profesor del colegio, o apoderado del estudiante
    if perfil.tipo_usuario == 'apoderado':
        if salida.estudiante.email_apoderado1 != perfil.user.email and salida.estudiante.email_apoderado2 != perfil.user.email:
            return HttpResponseForbidden()
    elif perfil.tipo_usuario in ['profesor', 'admin_colegio']:
        if salida.colegio != perfil.colegio:
            return HttpResponseForbidden()
    return render(request, 'salidas/detalle_salida.html', {'salida': salida})


@login_required
def buscar_estudiantes_salida(request):
    """Vista para buscar estudiantes mediante AJAX para el formulario de salidas"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse([], safe=False)

    # Obtener colegio del usuario si no es superusuario
    colegio = None
    if not request.user.is_superuser and hasattr(request.user, 'perfil'):
        colegio = request.user.perfil.colegio

    # Filtrar estudiantes (activo=True)
    estudiantes = Estudiante.objects.filter(
        Q(nombre__icontains=query) | Q(rut__icontains=query),
        activo=True
    )

    # Si no es superusuario, filtrar por colegio
    if colegio:
        estudiantes = estudiantes.filter(curso__colegio=colegio)

    # Limitar resultados
    estudiantes = estudiantes[:20]

    # Preparar datos para JSON
    results = []
    for estudiante in estudiantes:
        results.append({
            'id': estudiante.id,
            'nombre': estudiante.nombre,
            'rut': estudiante.rut,
            'curso': estudiante.curso.nombre  # Assuming curso has a nombre attribute
        })

    return JsonResponse(results, safe=False)


@login_required
def salida_delete(request, pk):
    salida = get_object_or_404(Salida, pk=pk)

    # Verificar permisos (superuser or admin_colegio of the same school)
    can_delete = False
    if request.user.is_superuser:
        can_delete = True
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        if hasattr(request.user.perfil, 'colegio'):
            # Ensure the salida's student's school matches the admin's school
            if salida.estudiante and salida.estudiante.curso and salida.estudiante.curso.colegio == request.user.perfil.colegio:
                can_delete = True

    if not can_delete:
        messages.error(request, 'No tienes permiso para eliminar esta salida.')
        return redirect('salidas:list')

    if request.method == 'POST':
        try:
            salida.delete()
            messages.success(request, 'Salida eliminada exitosamente.')
            return redirect('salidas:list')
        except Exception as e:
            messages.error(request, f'Error al eliminar la salida: {str(e)}')
            # Redirect back to list in case of error
            return redirect('salidas:list')

    return render(request, 'salidas/salida_confirm_delete.html', {
        'salida': salida
    })
