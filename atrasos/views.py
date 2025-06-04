from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Atraso
from .forms import AtrasoForm
from django.db.models import Q
from datetime import datetime, date
from django.http import JsonResponse
from estudiantes.models import Estudiante
from cursos.models import Curso


# Create your views here.


def puede_ver_atrasos(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.perfil.tipo_usuario in ['admin_colegio', 'profesor', 'apoderado']


@login_required
def atraso_list(request):
    # Obtener los atrasos según el tipo de usuario
    if request.user.is_superuser:
        atrasos = Atraso.objects.all()
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        atrasos = Atraso.objects.filter(
            estudiante__curso__colegio=request.user.perfil.colegio)
    elif request.user.perfil.tipo_usuario == 'profesor':
        atrasos = Atraso.objects.filter(
            estudiante__curso__colegio=request.user.perfil.colegio)
    else:
        messages.error(request, 'No tienes permiso para ver esta página.')
        return redirect('dashboard:index')

    # Filtrar por fecha si se proporciona
    fecha_filtro = request.GET.get('fecha')
    if fecha_filtro:
        try:
            fecha = datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
            atrasos = atrasos.filter(fecha=fecha)
        except ValueError:
            messages.error(request, 'Formato de fecha inválido')

    # Filtrar por búsqueda si se proporciona
    busqueda = request.GET.get('q')
    if busqueda:
        atrasos = atrasos.filter(
            Q(estudiante__nombre__icontains=busqueda) |
            Q(estudiante__rut__icontains=busqueda)
        )

    return render(request, 'atrasos/atraso_list.html', {
        'atrasos': atrasos,
        'fecha_filtro': fecha_filtro,
        'busqueda': busqueda
    })


@login_required
def atraso_create(request):
    if request.method == 'POST':
        form = AtrasoForm(request.POST)
        if form.is_valid():
            try:
                atraso = form.save(commit=False)
                atraso.estudiante = form.cleaned_data['rut_estudiante']
                atraso.save()
                messages.success(request, 'Atraso registrado exitosamente.')
                # return redirect('atrasos:list')
                return redirect('atrasos:imprimir', atraso.id)

            except Exception as e:
                messages.error(
                    request, f'Error al registrar el atraso: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        form = AtrasoForm()

    return render(request, 'atrasos/atraso_form.html', {
        'form': form,
        'title': 'Registrar Atraso'
    })


@login_required
def buscar_estudiantes(request):
    """Vista para buscar estudiantes mediante AJAX"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse([], safe=False)

    # Obtener colegio del usuario si no es superusuario
    colegio = None
    if not request.user.is_superuser and hasattr(request.user, 'perfil'):
        colegio = request.user.perfil.colegio

    # Filtrar estudiantes
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
            'curso': estudiante.curso.nombre
        })

    return JsonResponse(results, safe=False)


@login_required
def atraso_delete(request, pk):
    atraso = get_object_or_404(Atraso, pk=pk)

    # Verificar permisos (superuser o admin_colegio del mismo colegio)
    can_delete = False
    if request.user.is_superuser:
        can_delete = True
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        if hasattr(request.user.perfil, 'colegio'):
            # Asegurarse de que el colegio del atraso coincida con el del admin
            if atraso.estudiante and atraso.estudiante.curso and atraso.estudiante.curso.colegio == request.user.perfil.colegio:
                can_delete = True

    if not can_delete:
        messages.error(request, 'No tienes permiso para eliminar este atraso.')
        return redirect('atrasos:list')

    if request.method == 'POST':
        try:
            atraso.delete()
            messages.success(request, 'Atraso eliminado exitosamente.')
            return redirect('atrasos:list')
        except Exception as e:
            messages.error(request, f'Error al eliminar el atraso: {str(e)}')
            # Redirigir de nuevo a la lista en caso de error
            return redirect('atrasos:list')

    return render(request, 'atrasos/atraso_confirm_delete.html', {
        'atraso': atraso
    })


@login_required
@user_passes_test(puede_ver_atrasos)
def imprimir_atraso(request, atraso_id):
    atraso = get_object_or_404(Atraso, id=atraso_id)
    return render(request, 'atrasos/imprimir_atraso.html', {
        'atraso': atraso
    })


@login_required
def reportes_atraso(request):
    # Obtener los datos para el reporte
    atrasos = Atraso.objects.all()

    # Filtrar por fecha si se proporciona
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if fecha_inicio and fecha_fin:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            atrasos = atrasos.filter(fecha__range=[fecha_inicio, fecha_fin])
        except ValueError:
            messages.error(request, 'Formato de fecha inválido')
    elif fecha_inicio:  # Si solo se proporciona fecha inicio
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            atrasos = atrasos.filter(fecha__gte=fecha_inicio)
        except ValueError:
            messages.error(request, 'Formato de fecha inválido')
    elif fecha_fin:  # Si solo se proporciona fecha fin
        try:
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            atrasos = atrasos.filter(fecha__lte=fecha_fin)
        except ValueError:
            messages.error(request, 'Formato de fecha inválido')

    # Filtrar por estudiante si se proporciona
    estudiante_id = request.GET.get('estudiante')
    if estudiante_id:
        atrasos = atrasos.filter(estudiante_id=estudiante_id)

    # Filtrar por curso si se proporciona
    curso_id = request.GET.get('curso')
    if curso_id:
        atrasos = atrasos.filter(estudiante__curso_id=curso_id)

    # Filtrar por tipo de salida si se proporciona
    # tipo_salida = request.GET.get('tipo_salida')
    # if tipo_salida:
    #     salidas = salidas.filter(tipo_salida=tipo_salida)

    # Obtener lista de estudiantes para el filtro
    estudiantes = Estudiante.objects.filter(activo=True)

    # Obtener lista de cursos para el filtro
    cursos = Curso.objects.all()

    context = {
        'atrasos': atrasos,
        'estudiantes': estudiantes,
        'cursos': cursos,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'estudiante_id': estudiante_id,
        'curso_id': curso_id,
    }

    return render(request, 'atrasos/reportes_atraso.html', context)
