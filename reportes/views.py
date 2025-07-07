from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.template.loader import render_to_string
import json
import hashlib
import csv
from django.db import connection
from collections import defaultdict

# Importaciones para exportación
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows

# ReportLab para PDF (más compatible con Windows)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

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


# Funciones de exportación


@login_required
def exportar_reporte_pdf(request):
    """Exportar reporte en formato PDF"""
    # Obtener los mismos datos que el dashboard
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

    # Obtener datos
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

    # Top estudiantes
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

    context = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_atrasos': total_atrasos,
        'total_salidas': total_salidas,
        'atrasos_justificados': atrasos_justificados,
        'atrasos_no_justificados': atrasos_no_justificados,
        'porcentaje_justificados': round(porcentaje_justificados, 1),
        'porcentaje_no_justificados': round(porcentaje_no_justificados, 1),
        'atrasos_por_curso': list(atrasos_por_curso),
        'salidas_por_curso': list(salidas_por_curso),
        'top_estudiantes_atrasos': list(top_estudiantes_atrasos),
        'top_estudiantes_salidas': list(top_estudiantes_salidas),
        'fecha_generacion': timezone.now().strftime('%d/%m/%Y %H:%M'),
    }

    # Generar PDF con ReportLab
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []

    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#366092')
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.HexColor('#366092')
    )

    # Título principal
    story.append(
        Paragraph("REPORTE DE ANALYTICS - ATRASOS Y SALIDAS", title_style))
    story.append(Spacer(1, 20))

    # Información de filtros
    story.append(Paragraph("Filtros Aplicados:", heading_style))
    filtros_data = [
        ['Fecha inicio:', fecha_inicio or 'Todas las fechas'],
        ['Fecha fin:', fecha_fin or 'Todas las fechas'],
        ['Curso:', curso_id or 'Todos los cursos'],
        ['Fecha generación:', timezone.now().strftime('%d/%m/%Y %H:%M')]
    ]
    filtros_table = Table(filtros_data, colWidths=[2*inch, 4*inch])
    filtros_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(filtros_table)
    story.append(Spacer(1, 20))

    # Métricas principales
    story.append(Paragraph("Métricas Principales", heading_style))
    metrics_data = [
        ['Métrica', 'Valor'],
        ['Total Atrasos', str(total_atrasos)],
        ['Total Salidas', str(total_salidas)],
        ['Atrasos Justificados', str(atrasos_justificados)],
        ['Atrasos No Justificados', str(atrasos_no_justificados)],
        ['Porcentaje Justificados', f"{round(porcentaje_justificados, 1)}%"],
        ['Porcentaje No Justificados',
            f"{round(porcentaje_no_justificados, 1)}%"],
    ]
    metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 20))

    # Atrasos por curso
    story.append(Paragraph("Atrasos por Curso", heading_style))
    if atrasos_por_curso:
        atrasos_curso_data = [
            ['Curso', 'Total', 'Justificados', 'No Justificados']]
        for item in atrasos_por_curso:
            atrasos_curso_data.append([
                item['estudiante__curso__nombre'] or 'Curso desconocido',
                str(item['total']),
                str(item['justificados']),
                str(item['no_justificados'])
            ])
        atrasos_curso_table = Table(atrasos_curso_data, colWidths=[
                                    2.5*inch, 1*inch, 1.5*inch, 1.5*inch])
        atrasos_curso_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        story.append(atrasos_curso_table)
    else:
        story.append(Paragraph("No hay datos disponibles", styles['Normal']))
    story.append(Spacer(1, 20))

    # Salidas por curso
    story.append(Paragraph("Salidas por Curso", heading_style))
    if salidas_por_curso:
        salidas_curso_data = [['Curso', 'Total Salidas']]
        for item in salidas_por_curso:
            salidas_curso_data.append([
                item['estudiante__curso__nombre'] or 'Curso desconocido',
                str(item['total'])
            ])
        salidas_curso_table = Table(
            salidas_curso_data, colWidths=[4*inch, 2*inch])
        salidas_curso_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        story.append(salidas_curso_table)
    else:
        story.append(Paragraph("No hay datos disponibles", styles['Normal']))
    story.append(PageBreak())

    # Top estudiantes atrasos
    story.append(
        Paragraph("Top 10 - Estudiantes con Más Atrasos", heading_style))
    if top_estudiantes_atrasos:
        top_atrasos_data = [['Estudiante', 'RUT', 'Curso',
                             'Total Atrasos', 'Justificados', 'No Justificados']]
        for item in top_estudiantes_atrasos:
            top_atrasos_data.append([
                item['estudiante__nombre'],
                item['estudiante__rut'],
                item['estudiante__curso__nombre'],
                str(item['total_atrasos']),
                str(item['atrasos_justificados']),
                str(item['atrasos_no_justificados'])
            ])
        top_atrasos_table = Table(top_atrasos_data, colWidths=[
                                  1.5*inch, 1*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
        top_atrasos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        story.append(top_atrasos_table)
    else:
        story.append(Paragraph("No hay datos disponibles", styles['Normal']))
    story.append(Spacer(1, 20))

    # Top estudiantes salidas
    story.append(
        Paragraph("Top 10 - Estudiantes con Más Salidas", heading_style))
    if top_estudiantes_salidas:
        top_salidas_data = [['Estudiante', 'RUT', 'Curso', 'Total Salidas']]
        for item in top_estudiantes_salidas:
            top_salidas_data.append([
                item['estudiante__nombre'],
                item['estudiante__rut'],
                item['estudiante__curso__nombre'],
                str(item['total_salidas'])
            ])
        top_salidas_table = Table(top_salidas_data, colWidths=[
                                  2*inch, 1*inch, 2*inch, 1*inch])
        top_salidas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        story.append(top_salidas_table)
    else:
        story.append(Paragraph("No hay datos disponibles", styles['Normal']))

    # Generar PDF
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()

    # Crear respuesta HTTP
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_analytics_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf"'

    return response


@login_required
def exportar_reporte_excel(request):
    """Exportar reporte en formato Excel"""
    # Obtener los mismos datos que el dashboard
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

    # Obtener datos
    atrasos = Atraso.objects.filter(filtros_atrasos)
    salidas = Salida.objects.filter(filtros_salidas)

    # Métricas principales
    total_atrasos = atrasos.count()
    total_salidas = salidas.count()
    atrasos_justificados = atrasos.filter(justificado=True).count()
    atrasos_no_justificados = atrasos.filter(justificado=False).count()

    # Análisis por curso
    atrasos_por_curso = atrasos.values('estudiante__curso__nombre').annotate(
        total=Count('id'),
        justificados=Count('id', filter=Q(justificado=True)),
        no_justificados=Count('id', filter=Q(justificado=False))
    ).order_by('-total')

    salidas_por_curso = salidas.values('estudiante__curso__nombre').annotate(
        total=Count('id')
    ).order_by('-total')

    # Top estudiantes
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

    # Crear workbook de Excel
    wb = Workbook()

    # Hoja 1: Resumen
    ws1 = wb.active
    ws1.title = "Resumen"

    # Estilos
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092",
                              end_color="366092", fill_type="solid")
    center_alignment = Alignment(horizontal="center", vertical="center")

    # Título
    ws1['A1'] = "REPORTE DE ANALYTICS - ATRASOS Y SALIDAS"
    ws1['A1'].font = Font(bold=True, size=16)
    ws1.merge_cells('A1:E1')

    # Filtros aplicados
    ws1['A3'] = "Filtros aplicados:"
    ws1['A3'].font = Font(bold=True)
    ws1['A4'] = f"Fecha inicio: {fecha_inicio or 'Todas'}"
    ws1['A5'] = f"Fecha fin: {fecha_fin or 'Todas'}"
    ws1['A6'] = f"Curso: {curso_id or 'Todos'}"
    ws1['A7'] = f"Fecha generación: {timezone.now().strftime('%d/%m/%Y %H:%M')}"

    # Métricas principales
    ws1['A9'] = "MÉTRICAS PRINCIPALES"
    ws1['A9'].font = Font(bold=True, size=14)

    headers = ['Métrica', 'Valor']
    for col, header in enumerate(headers, 1):
        cell = ws1.cell(row=10, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment

    metrics_data = [
        ['Total Atrasos', total_atrasos],
        ['Total Salidas', total_salidas],
        ['Atrasos Justificados', atrasos_justificados],
        ['Atrasos No Justificados', atrasos_no_justificados],
        ['Porcentaje Justificados',
            f"{round((atrasos_justificados / total_atrasos * 100) if total_atrasos > 0 else 0, 1)}%"],
        ['Porcentaje No Justificados',
            f"{round((atrasos_no_justificados / total_atrasos * 100) if total_atrasos > 0 else 0, 1)}%"],
    ]

    for row, (metric, value) in enumerate(metrics_data, 11):
        ws1.cell(row=row, column=1, value=metric)
        ws1.cell(row=row, column=2, value=value)

    # Hoja 2: Atrasos por Curso
    ws2 = wb.create_sheet("Atrasos por Curso")

    headers = ['Curso', 'Total', 'Justificados', 'No Justificados']
    for col, header in enumerate(headers, 1):
        cell = ws2.cell(row=1, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment

    for row, item in enumerate(atrasos_por_curso, 2):
        ws2.cell(row=row, column=1,
                 value=item['estudiante__curso__nombre'] or 'Curso desconocido')
        ws2.cell(row=row, column=2, value=item['total'])
        ws2.cell(row=row, column=3, value=item['justificados'])
        ws2.cell(row=row, column=4, value=item['no_justificados'])

    # Hoja 3: Salidas por Curso
    ws3 = wb.create_sheet("Salidas por Curso")

    headers = ['Curso', 'Total Salidas']
    for col, header in enumerate(headers, 1):
        cell = ws3.cell(row=1, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment

    for row, item in enumerate(salidas_por_curso, 2):
        ws3.cell(row=row, column=1,
                 value=item['estudiante__curso__nombre'] or 'Curso desconocido')
        ws3.cell(row=row, column=2, value=item['total'])

    # Hoja 4: Top Estudiantes Atrasos
    ws4 = wb.create_sheet("Top Atrasos")

    headers = ['Estudiante', 'RUT', 'Curso',
               'Total Atrasos', 'Justificados', 'No Justificados']
    for col, header in enumerate(headers, 1):
        cell = ws4.cell(row=1, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment

    for row, item in enumerate(top_estudiantes_atrasos, 2):
        ws4.cell(row=row, column=1, value=item['estudiante__nombre'])
        ws4.cell(row=row, column=2, value=item['estudiante__rut'])
        ws4.cell(row=row, column=3, value=item['estudiante__curso__nombre'])
        ws4.cell(row=row, column=4, value=item['total_atrasos'])
        ws4.cell(row=row, column=5, value=item['atrasos_justificados'])
        ws4.cell(row=row, column=6, value=item['atrasos_no_justificados'])

    # Hoja 5: Top Estudiantes Salidas
    ws5 = wb.create_sheet("Top Salidas")

    headers = ['Estudiante', 'RUT', 'Curso', 'Total Salidas']
    for col, header in enumerate(headers, 1):
        cell = ws5.cell(row=1, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment

    for row, item in enumerate(top_estudiantes_salidas, 2):
        ws5.cell(row=row, column=1, value=item['estudiante__nombre'])
        ws5.cell(row=row, column=2, value=item['estudiante__rut'])
        ws5.cell(row=row, column=3, value=item['estudiante__curso__nombre'])
        ws5.cell(row=row, column=4, value=item['total_salidas'])

        # Ajustar ancho de columnas de forma segura
    def adjust_column_widths(worksheet):
        """Ajusta el ancho de las columnas de forma segura"""
        # Convertir número de columna a letra de forma manual
        def get_column_letter(col_num):
            """Convierte número de columna a letra (A, B, C, ..., Z, AA, AB, etc.)"""
            result = ""
            while col_num > 0:
                col_num, remainder = divmod(col_num - 1, 26)
                result = chr(65 + remainder) + result
            return result

        for col_num in range(1, worksheet.max_column + 1):
            max_length = 0
            column_letter = get_column_letter(col_num)

            # Calcular el ancho máximo de la columna
            for row_num in range(1, worksheet.max_row + 1):
                try:
                    cell = worksheet.cell(row=row_num, column=col_num)
                    if cell.value:
                        cell_length = len(str(cell.value))
                        if cell_length > max_length:
                            max_length = cell_length
                except:
                    pass

            # Ajustar ancho con un mínimo y máximo
            adjusted_width = min(max(max_length + 2, 8), 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    # Aplicar ajuste de columnas a todas las hojas
    for ws in [ws1, ws2, ws3, ws4, ws5]:
        adjust_column_widths(ws)

    # Guardar archivo
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="reporte_analytics_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'

    wb.save(response)
    return response


@login_required
def exportar_reporte_csv(request):
    """Exportar reporte en formato CSV"""
    # Obtener los mismos datos que el dashboard
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

    # Obtener datos
    atrasos = Atraso.objects.filter(filtros_atrasos)
    salidas = Salida.objects.filter(filtros_salidas)

    # Análisis por curso
    atrasos_por_curso = atrasos.values('estudiante__curso__nombre').annotate(
        total=Count('id'),
        justificados=Count('id', filter=Q(justificado=True)),
        no_justificados=Count('id', filter=Q(justificado=False))
    ).order_by('-total')

    salidas_por_curso = salidas.values('estudiante__curso__nombre').annotate(
        total=Count('id')
    ).order_by('-total')

    # Top estudiantes
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

    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="reporte_analytics_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'

    # Configurar writer con encoding UTF-8
    response.write('\ufeff')  # BOM para Excel
    writer = csv.writer(response)

    # Información del reporte
    writer.writerow(['REPORTE DE ANALYTICS - ATRASOS Y SALIDAS'])
    writer.writerow([])
    writer.writerow(['Filtros aplicados:'])
    writer.writerow([f'Fecha inicio: {fecha_inicio or "Todas"}'])
    writer.writerow([f'Fecha fin: {fecha_fin or "Todas"}'])
    writer.writerow([f'Curso: {curso_id or "Todos"}'])
    writer.writerow(
        [f'Fecha generación: {timezone.now().strftime("%d/%m/%Y %H:%M")}'])
    writer.writerow([])

    # Atrasos por curso
    writer.writerow(['ATRASOS POR CURSO'])
    writer.writerow(['Curso', 'Total', 'Justificados', 'No Justificados'])
    for item in atrasos_por_curso:
        writer.writerow([
            item['estudiante__curso__nombre'] or 'Curso desconocido',
            item['total'],
            item['justificados'],
            item['no_justificados']
        ])
    writer.writerow([])

    # Salidas por curso
    writer.writerow(['SALIDAS POR CURSO'])
    writer.writerow(['Curso', 'Total Salidas'])
    for item in salidas_por_curso:
        writer.writerow([
            item['estudiante__curso__nombre'] or 'Curso desconocido',
            item['total']
        ])
    writer.writerow([])

    # Top estudiantes atrasos
    writer.writerow(['TOP 10 ESTUDIANTES CON MÁS ATRASOS'])
    writer.writerow(['Estudiante', 'RUT', 'Curso',
                    'Total Atrasos', 'Justificados', 'No Justificados'])
    for item in top_estudiantes_atrasos:
        writer.writerow([
            item['estudiante__nombre'],
            item['estudiante__rut'],
            item['estudiante__curso__nombre'],
            item['total_atrasos'],
            item['atrasos_justificados'],
            item['atrasos_no_justificados']
        ])
    writer.writerow([])

    # Top estudiantes salidas
    writer.writerow(['TOP 10 ESTUDIANTES CON MÁS SALIDAS'])
    writer.writerow(['Estudiante', 'RUT', 'Curso', 'Total Salidas'])
    for item in top_estudiantes_salidas:
        writer.writerow([
            item['estudiante__nombre'],
            item['estudiante__rut'],
            item['estudiante__curso__nombre'],
            item['total_salidas']
        ])

    return response
