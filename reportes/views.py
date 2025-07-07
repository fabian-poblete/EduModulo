from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
import json
import hashlib
from django.db import connection
from collections import defaultdict

from atrasos.models import Atraso
from salidas.models import Salida
from estudiantes.models import Estudiante
from cursos.models import Curso
from colegios.models import Colegio


@login_required
def dashboard_analytics(request):
    """Dashboard principal de analytics con filtros dinámicos"""

    # Obtener filtros de la URL
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    curso_id = request.GET.get('curso')
    tipo_incidencia = request.GET.get('tipo_incidencia', 'todos')

    # Aplicar filtros base
    filtros_atrasos = Q()
    filtros_salidas = Q()

    if fecha_inicio:
        filtros_atrasos &= Q(fecha__gte=fecha_inicio)
        filtros_salidas &= Q(fecha__gte=fecha_inicio)

    if fecha_fin:
        filtros_atrasos &= Q(fecha__lte=fecha_fin)
        filtros_salidas &= Q(fecha__lte=fecha_fin)

    if curso_id:
        filtros_atrasos &= Q(estudiante__curso_id=curso_id)
        filtros_salidas &= Q(estudiante__curso_id=curso_id)

    # Obtener datos de atrasos
    atrasos = Atraso.objects.filter(filtros_atrasos)
    salidas = Salida.objects.filter(filtros_salidas)

    # Métricas principales
    total_atrasos = atrasos.count()
    total_salidas = salidas.count()
    atrasos_justificados = atrasos.filter(justificado=True).count()
    atrasos_no_justificados = atrasos.filter(justificado=False).count()

    # Porcentajes
    porcentaje_justificados = (
        atrasos_justificados / total_atrasos * 100) if total_atrasos > 0 else 0
    porcentaje_no_justificados = (
        atrasos_no_justificados / total_atrasos * 100) if total_atrasos > 0 else 0

    # Análisis por curso
    atrasos_por_curso = atrasos.values('estudiante__curso__nombre').annotate(
        total=Count('id'),
        justificados=Count('id', filter=Q(justificado=True)),
        no_justificados=Count('id', filter=Q(justificado=False))
    ).order_by('-total')

    salidas_por_curso = salidas.values('estudiante__curso__nombre').annotate(
        total=Count('id')
    ).order_by('-total')

    # Análisis temporal
    # Agrupamiento temporal compatible con SQLite y PostgreSQL
    if connection.vendor == 'sqlite':
        # Agrupar atrasos por fecha en Python
        atrasos_por_fecha_dict = defaultdict(
            lambda: {'total': 0, 'justificados': 0, 'no_justificados': 0})
        for atraso in atrasos:
            fecha = atraso.fecha
            atrasos_por_fecha_dict[fecha]['total'] += 1
            if atraso.justificado:
                atrasos_por_fecha_dict[fecha]['justificados'] += 1
            else:
                atrasos_por_fecha_dict[fecha]['no_justificados'] += 1
        atrasos_por_fecha = [
            {'fecha_simple': fecha, **data}
            for fecha, data in sorted(atrasos_por_fecha_dict.items())
        ]
        # Agrupar salidas por fecha en Python
        salidas_por_fecha_dict = defaultdict(lambda: {'total': 0})
        for salida in salidas:
            fecha = salida.fecha
            salidas_por_fecha_dict[fecha]['total'] += 1
        salidas_por_fecha = [
            {'fecha_simple': fecha, **data}
            for fecha, data in sorted(salidas_por_fecha_dict.items())
        ]
    else:
        atrasos_por_fecha = atrasos.annotate(
            fecha_simple=TruncDate('fecha')
        ).values('fecha_simple').annotate(
            total=Count('id'),
            justificados=Count('id', filter=Q(justificado=True)),
            no_justificados=Count('id', filter=Q(justificado=False))
        ).order_by('fecha_simple')
        salidas_por_fecha = salidas.annotate(
            fecha_simple=TruncDate('fecha')
        ).values('fecha_simple').annotate(
            total=Count('id')
        ).order_by('fecha_simple')

    # Top estudiantes con más incidencias
    top_estudiantes_atrasos = atrasos.values(
        'estudiante__nombre', 'estudiante__rut', 'estudiante__curso__nombre'
    ).annotate(
        total_atrasos=Count('id'),
        atrasos_justificados=Count('id', filter=Q(justificado=True)),
        atrasos_no_justificados=Count('id', filter=Q(justificado=False))
    ).order_by('-total_atrasos')[:10]

    top_estudiantes_salidas = salidas.values(
        'estudiante__nombre', 'estudiante__rut', 'estudiante__curso__nombre'
    ).annotate(
        total_salidas=Count('id')
    ).order_by('-total_salidas')[:10]

    # Análisis por hora del día
    atrasos_por_hora = atrasos.values('hora').annotate(
        total=Count('id')
    ).order_by('hora')

    # Preparar datos para JavaScript - convertir fechas a strings y manejar valores nulos
    def prepare_data_for_js(data_list):
        """Convierte los datos para que sean compatibles con JavaScript"""
        prepared_data = []
        for item in data_list:
            prepared_item = {}
            for key, value in item.items():
                if hasattr(value, 'strftime'):  # Es una fecha
                    prepared_item[key] = value.strftime('%Y-%m-%d')
                elif value is None:
                    prepared_item[key] = ''
                else:
                    prepared_item[key] = value
            prepared_data.append(prepared_item)
        return prepared_data

    # Contexto para el template
    context = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'curso_id': curso_id,
        'tipo_incidencia': tipo_incidencia,

        # Métricas principales
        'total_atrasos': total_atrasos,
        'total_salidas': total_salidas,
        'atrasos_justificados': atrasos_justificados,
        'atrasos_no_justificados': atrasos_no_justificados,
        'porcentaje_justificados': round(porcentaje_justificados, 1),
        'porcentaje_no_justificados': round(porcentaje_no_justificados, 1),

        # Datos para gráficos - serializados para JavaScript
        'atrasos_por_curso': json.dumps(prepare_data_for_js(list(atrasos_por_curso))),
        'salidas_por_curso': json.dumps(prepare_data_for_js(list(salidas_por_curso))),
        'atrasos_por_fecha': json.dumps(prepare_data_for_js(list(atrasos_por_fecha))),
        'salidas_por_fecha': json.dumps(prepare_data_for_js(list(salidas_por_fecha))),
        'atrasos_por_hora': json.dumps(prepare_data_for_js(list(atrasos_por_hora))),

        # Top estudiantes
        'top_estudiantes_atrasos': list(top_estudiantes_atrasos),
        'top_estudiantes_salidas': list(top_estudiantes_salidas),

        # Filtros disponibles
        'cursos': Curso.objects.all().order_by('nombre'),
    }

    return render(request, 'reportes/dashboard_analytics.html', context)


@login_required
def api_datos_graficos(request):
    """API para obtener datos de gráficos en formato JSON"""

    # Obtener parámetros
    tipo_grafico = request.GET.get('tipo')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    curso_id = request.GET.get('curso')

    # Aplicar filtros
    filtros_atrasos = Q()
    filtros_salidas = Q()

    if fecha_inicio:
        filtros_atrasos &= Q(fecha__gte=fecha_inicio)
        filtros_salidas &= Q(fecha__gte=fecha_inicio)

    if fecha_fin:
        filtros_atrasos &= Q(fecha__lte=fecha_fin)
        filtros_salidas &= Q(fecha__lte=fecha_fin)

    if curso_id:
        filtros_atrasos &= Q(estudiante__curso_id=curso_id)
        filtros_salidas &= Q(estudiante__curso_id=curso_id)

    atrasos = Atraso.objects.filter(filtros_atrasos)
    salidas = Salida.objects.filter(filtros_salidas)

    if tipo_grafico == 'atrasos_por_curso':
        datos = atrasos.values('estudiante__curso__nombre').annotate(
            total=Count('id'),
            justificados=Count('id', filter=Q(justificado=True)),
            no_justificados=Count('id', filter=Q(justificado=False))
        ).order_by('-total')

    elif tipo_grafico == 'salidas_por_curso':
        datos = salidas.values('estudiante__curso__nombre').annotate(
            total=Count('id')
        ).order_by('-total')

    elif tipo_grafico == 'atrasos_temporales':
        datos = atrasos.annotate(
            fecha_simple=TruncDate('fecha')
        ).values('fecha_simple').annotate(
            total=Count('id'),
            justificados=Count('id', filter=Q(justificado=True)),
            no_justificados=Count('id', filter=Q(justificado=False))
        ).order_by('fecha_simple')

    elif tipo_grafico == 'salidas_temporales':
        datos = salidas.annotate(
            fecha_simple=TruncDate('fecha')
        ).values('fecha_simple').annotate(
            total=Count('id')
        ).order_by('fecha_simple')

    elif tipo_grafico == 'atrasos_por_hora':
        datos = atrasos.values('hora').annotate(
            total=Count('id')
        ).order_by('hora')

    else:
        datos = []

    return JsonResponse({'datos': list(datos)})


@login_required
def reporte_detallado(request):
    """Reporte detallado con análisis profundo"""

    # Obtener filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    curso_id = request.GET.get('curso')
    tipo_analisis = request.GET.get('tipo_analisis', 'general')

    # Aplicar filtros
    filtros_atrasos = Q()
    filtros_salidas = Q()

    if fecha_inicio:
        filtros_atrasos &= Q(fecha__gte=fecha_inicio)
        filtros_salidas &= Q(fecha__gte=fecha_inicio)

    if fecha_fin:
        filtros_atrasos &= Q(fecha__lte=fecha_fin)
        filtros_salidas &= Q(fecha__lte=fecha_fin)

    if curso_id:
        filtros_atrasos &= Q(estudiante__curso_id=curso_id)
        filtros_salidas &= Q(estudiante__curso_id=curso_id)

    atrasos = Atraso.objects.filter(filtros_atrasos)
    salidas = Salida.objects.filter(filtros_salidas)

    # Análisis detallado según tipo
    if tipo_analisis == 'tendencias':
        if connection.vendor == 'sqlite':
            # Agrupar atrasos por mes en Python
            atrasos_tendencias_dict = defaultdict(
                lambda: {'total': 0, 'justificados': 0, 'no_justificados': 0})
            for atraso in atrasos:
                mes = atraso.fecha.replace(day=1)
                atrasos_tendencias_dict[mes]['total'] += 1
                if atraso.justificado:
                    atrasos_tendencias_dict[mes]['justificados'] += 1
                else:
                    atrasos_tendencias_dict[mes]['no_justificados'] += 1
            atrasos_tendencias = [
                {'mes': mes, **data}
                for mes, data in sorted(atrasos_tendencias_dict.items())
            ]
            # Agrupar salidas por mes en Python
            salidas_tendencias_dict = defaultdict(lambda: {'total': 0})
            for salida in salidas:
                mes = salida.fecha.replace(day=1)
                salidas_tendencias_dict[mes]['total'] += 1
            salidas_tendencias = [
                {'mes': mes, **data}
                for mes, data in sorted(salidas_tendencias_dict.items())
            ]
        else:
            atrasos_tendencias = atrasos.annotate(
                mes=TruncMonth('fecha')
            ).values('mes').annotate(
                total=Count('id'),
                justificados=Count('id', filter=Q(justificado=True)),
                no_justificados=Count('id', filter=Q(justificado=False))
            ).order_by('mes')
            salidas_tendencias = salidas.annotate(
                mes=TruncMonth('fecha')
            ).values('mes').annotate(
                total=Count('id')
            ).order_by('mes')
        datos_analisis = {
            'atrasos_tendencias': list(atrasos_tendencias),
            'salidas_tendencias': list(salidas_tendencias),
        }

    elif tipo_analisis == 'comportamiento':
        # Análisis de comportamiento por estudiante
        comportamiento_estudiantes = atrasos.values(
            'estudiante__nombre', 'estudiante__rut', 'estudiante__curso__nombre'
        ).annotate(
            total_atrasos=Count('id'),
            atrasos_justificados=Count('id', filter=Q(justificado=True)),
            atrasos_no_justificados=Count('id', filter=Q(justificado=False)),
            porcentaje_justificados=Avg('justificado') * 100
        ).order_by('-total_atrasos')

        datos_analisis = {
            'comportamiento_estudiantes': list(comportamiento_estudiantes),
        }

    else:  # general
        # Análisis general
        datos_analisis = {
            'total_atrasos': atrasos.count(),
            'total_salidas': salidas.count(),
            'atrasos_justificados': atrasos.filter(justificado=True).count(),
            'atrasos_no_justificados': atrasos.filter(justificado=False).count(),
        }

    context = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'curso_id': curso_id,
        'tipo_analisis': tipo_analisis,
        'datos_analisis': datos_analisis,
        'cursos': Curso.objects.all().order_by('nombre'),
    }

    return render(request, 'reportes/reporte_detallado.html', context)
