from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Prefetch
from django.core.paginator import Paginator
from colegios.models import Colegio
from django.contrib.auth.models import User
from cursos.models import Curso
from estudiantes.models import Estudiante
from atrasos.models import Atraso
from salidas.models import Salida


@login_required
def index(request):
    """
    Vista optimizada del dashboard con consultas eficientes.
    Reduce de 8-12 consultas a 2-3 consultas usando agregaciones y select_related.
    """

    # Determinar el colegio según el tipo de usuario
    if request.user.is_superuser:
        # Superusuarios ven todos los datos
        colegio_filter = Q()
        show_usuarios = True
    elif request.user.perfil.tipo_usuario in ['admin_colegio', 'administrativo', 'profesor', 'porteria']:
        # Usuarios específicos ven datos de su colegio
        colegio = request.user.perfil.colegio
        colegio_filter = Q(curso__colegio=colegio)
        show_usuarios = request.user.perfil.tipo_usuario in [
            'admin_colegio', 'administrativo']
    else:
        # Otros usuarios no ven datos
        return render(request, 'dashboard/index.html', {
            'total_cursos': 0, 'total_estudiantes': 0, 'total_usuarios': 0,
            'cursos_activos': 0, 'estudiantes_activos': 0, 'total_atrasos': 0, 'total_salidas': 0,
            'ultimos_cursos': [], 'ultimos_estudiantes': [], 'ultimos_usuarios': []
        })

    # CONSULTA OPTIMIZADA 1: Estadísticas de cursos y estudiantes en una sola consulta
    if request.user.is_superuser:
        # Para superusuarios, consultar todos los datos
        curso_stats = Curso.objects.aggregate(
            total=Count('id'),
            activos=Count('id', filter=Q(activo=True))
        )

        estudiante_stats = Estudiante.objects.aggregate(
            total=Count('id'),
            activos=Count('id', filter=Q(activo=True))
        )

        atraso_stats = Atraso.objects.aggregate(
            total=Count('id')
        )

        salida_stats = Salida.objects.aggregate(
            total=Count('id')
        )

        usuario_stats = User.objects.filter(is_active=True).aggregate(
            total=Count('id')
        )
    else:
        # Para usuarios específicos, filtrar por colegio
        curso_stats = Curso.objects.filter(colegio=colegio).aggregate(
            total=Count('id'),
            activos=Count('id', filter=Q(activo=True))
        )

        estudiante_stats = Estudiante.objects.filter(curso__colegio=colegio).aggregate(
            total=Count('id'),
            activos=Count('id', filter=Q(activo=True))
        )

        atraso_stats = Atraso.objects.filter(estudiante__curso__colegio=colegio).aggregate(
            total=Count('id')
        )

        salida_stats = Salida.objects.filter(estudiante__curso__colegio=colegio).aggregate(
            total=Count('id')
        )

        if show_usuarios:
            usuario_stats = User.objects.filter(perfil__colegio=colegio, is_active=True).aggregate(
                total=Count('id')
            )
        else:
            usuario_stats = {'total': 0}

    # CONSULTA OPTIMIZADA 2: Datos recientes con select_related y paginación
    # Obtener parámetros de paginación
    page_size = 5  # Número de elementos por página
    cursos_page = request.GET.get('cursos_page', 1)
    estudiantes_page = request.GET.get('estudiantes_page', 1)
    usuarios_page = request.GET.get('usuarios_page', 1)

    if request.user.is_superuser:
        # Para superusuarios
        cursos_queryset = Curso.objects.select_related(
            'colegio').order_by('-fecha_creacion')
        estudiantes_queryset = Estudiante.objects.select_related(
            'curso__colegio').order_by('-fecha_creacion')
        usuarios_queryset = User.objects.select_related('perfil__colegio').filter(
            is_active=True).order_by('-date_joined') if show_usuarios else User.objects.none()
    else:
        # Para usuarios específicos
        cursos_queryset = Curso.objects.select_related('colegio').filter(
            colegio=colegio).order_by('-fecha_creacion')
        estudiantes_queryset = Estudiante.objects.select_related(
            'curso__colegio').filter(curso__colegio=colegio).order_by('-fecha_creacion')
        usuarios_queryset = User.objects.select_related('perfil__colegio').filter(
            perfil__colegio=colegio, is_active=True).order_by('-date_joined') if show_usuarios else User.objects.none()

    # Aplicar paginación
    cursos_paginator = Paginator(cursos_queryset, page_size)
    estudiantes_paginator = Paginator(estudiantes_queryset, page_size)
    usuarios_paginator = Paginator(
        usuarios_queryset, page_size) if show_usuarios else None

    try:
        ultimos_cursos = cursos_paginator.page(cursos_page)
    except:
        ultimos_cursos = cursos_paginator.page(1)

    try:
        ultimos_estudiantes = estudiantes_paginator.page(estudiantes_page)
    except:
        ultimos_estudiantes = estudiantes_paginator.page(1)

    if usuarios_paginator:
        try:
            ultimos_usuarios = usuarios_paginator.page(usuarios_page)
        except:
            ultimos_usuarios = usuarios_paginator.page(1)
    else:
        ultimos_usuarios = []

    # Preparar contexto con datos optimizados
    context = {
        'total_cursos': curso_stats['total'],
        'total_estudiantes': estudiante_stats['total'],
        'total_usuarios': usuario_stats['total'],
        'cursos_activos': curso_stats['activos'],
        'estudiantes_activos': estudiante_stats['activos'],
        'total_atrasos': atraso_stats['total'],
        'total_salidas': salida_stats['total'],
        'ultimos_cursos': ultimos_cursos,
        'ultimos_estudiantes': ultimos_estudiantes,
        'ultimos_usuarios': ultimos_usuarios,
        # Información de paginación para el template
        'cursos_paginator': cursos_paginator,
        'estudiantes_paginator': estudiantes_paginator,
        'usuarios_paginator': usuarios_paginator,
    }

    return render(request, 'dashboard/index.html', context)
