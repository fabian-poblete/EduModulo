from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Estudiante, Curso
from .forms import EstudianteForm
from django.http import HttpResponse
import pandas as pd
from datetime import datetime
import os
import re

# Create your views here.


@login_required
def estudiante_list(request):
    # Superusuarios ven todos los estudiantes
    if request.user.is_superuser:
        estudiantes = Estudiante.objects.all()
        can_edit = True
    # Admin de colegio ve estudiantes de su colegio
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        estudiantes = Estudiante.objects.filter(
            curso__colegio=request.user.perfil.colegio)
        can_edit = True
    # Profesores ven estudiantes de su colegio pero no pueden editar
    elif request.user.perfil.tipo_usuario == 'profesor':
        estudiantes = Estudiante.objects.filter(
            curso__colegio=request.user.perfil.colegio)
        can_edit = False
    else:
        messages.error(request, 'No tienes permiso para ver esta página.')
        return redirect('dashboard:index')

    return render(request, 'estudiantes/estudiante_list.html', {
        'estudiantes': estudiantes,
        'can_edit': can_edit
    })


@login_required
def estudiante_create(request, colegio_id=None):
    # Verificar permisos
    if not (request.user.is_superuser or request.user.perfil.tipo_usuario == 'admin_colegio'):
        messages.error(request, 'No tienes permiso para crear estudiantes.')
        return redirect('estudiantes:list')

    if request.method == 'POST':
        form = EstudianteForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                estudiante = form.save(commit=False)
                estudiante.activo = True
                estudiante.save()
                messages.success(request, 'Estudiante creado exitosamente.')
                return redirect('estudiantes:list')
            except Exception as e:
                messages.error(
                    request, f'Error al crear el estudiante: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        form = EstudianteForm(user=request.user)

    return render(request, 'estudiantes/estudiante_form.html', {
        'form': form,
        'title': 'Crear Estudiante'
    })


@login_required
def estudiante_update(request, pk):
    estudiante = get_object_or_404(Estudiante, pk=pk)

    # Verificar permisos
    if request.user.is_superuser:
        can_edit = True
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        can_edit = estudiante.curso.colegio == request.user.perfil.colegio
    else:
        can_edit = False

    if not can_edit:
        messages.error(
            request, 'No tienes permiso para editar este estudiante.')
        return redirect('estudiantes:list')

    if request.method == 'POST':
        form = EstudianteForm(
            request.POST, instance=estudiante, user=request.user)
        if form.is_valid():
            try:
                form.save()
                messages.success(
                    request, 'Estudiante actualizado exitosamente.')
                return redirect('estudiantes:list')
            except Exception as e:
                messages.error(
                    request, f'Error al actualizar el estudiante: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        form = EstudianteForm(instance=estudiante, user=request.user)

    return render(request, 'estudiantes/estudiante_form.html', {
        'form': form,
        'title': 'Editar Estudiante',
        'is_edit': True
    })


@login_required
def estudiante_delete(request, pk):
    estudiante = get_object_or_404(Estudiante, pk=pk)

    # Verificar permisos
    if request.user.is_superuser:
        can_delete = True
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        can_delete = estudiante.curso.colegio == request.user.perfil.colegio
    else:
        can_delete = False

    if not can_delete:
        messages.error(
            request, 'No tienes permiso para eliminar este estudiante.')
        return redirect('estudiantes:list')

    if request.method == 'POST':
        try:
            estudiante.delete()
            messages.success(request, 'Estudiante eliminado exitosamente.')
            return redirect('estudiantes:list')
        except Exception as e:
            messages.error(
                request, f'Error al eliminar el estudiante: {str(e)}')

    return render(request, 'estudiantes/estudiante_confirm_delete.html', {
        'estudiante': estudiante
    })


def validar_rut(rut):
    """
    Valida el RUT chileno y retorna el RUT formateado si es válido.
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
        # Formatear RUT con puntos y guión
        rut_formateado = f"{int(numero):,}".replace(',', '.') + '-' + dv
        return rut_formateado
    return None


@login_required
def carga_masiva(request):
    if not request.user.is_superuser and request.user.perfil.tipo_usuario != 'admin_colegio':
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('estudiantes:list')

    if request.method == 'POST':
        if 'archivo' not in request.FILES:
            messages.error(request, 'No se ha seleccionado ningún archivo.')
            return redirect('estudiantes:carga_masiva')

        archivo = request.FILES['archivo']
        if not archivo.name.endswith('.xlsx'):
            messages.error(request, 'El archivo debe ser un Excel (.xlsx)')
            return redirect('estudiantes:carga_masiva')

        try:
            # Leer el archivo Excel
            df = pd.read_excel(archivo)

            # Validar columnas requeridas
            columnas_requeridas = ['nombre', 'rut', 'curso', 'email_estudiante',
                                   'email_apoderado1', 'email_apoderado2', 'telefono_apoderado1', 'telefono_apoderado2']
            for col in columnas_requeridas:
                if col not in df.columns:
                    messages.error(
                        request, f'El archivo debe contener la columna: {col}')
                    return redirect('estudiantes:carga_masiva')

            # Obtener el colegio del usuario
            colegio = request.user.perfil.colegio if not request.user.is_superuser else None

            # Procesar cada fila
            exitosos = 0
            errores = []

            for index, row in df.iterrows():
                try:
                    # Validar RUT
                    rut = str(row['rut']).strip()
                    rut_validado = validar_rut(rut)
                    if not rut_validado:
                        raise Exception(f'RUT inválido: {rut}')

                    # Buscar el curso por nombre
                    curso_nombre = str(row['curso']).strip()
                    if colegio:
                        curso = Curso.objects.filter(
                            nombre=curso_nombre, colegio=colegio).first()
                    else:
                        curso = Curso.objects.filter(
                            nombre=curso_nombre).first()

                    if not curso:
                        raise Exception(
                            f'No se encontró el curso: {curso_nombre}')

                    # Crear o actualizar estudiante
                    estudiante, created = Estudiante.objects.update_or_create(
                        rut=rut_validado,
                        defaults={
                            'nombre': row['nombre'],
                            'curso': curso,
                            'email_estudiante': row['email_estudiante'] if pd.notna(row['email_estudiante']) else None,
                            'email_apoderado1': row['email_apoderado1'] if pd.notna(row['email_apoderado1']) else None,
                            'email_apoderado2': row['email_apoderado2'] if pd.notna(row['email_apoderado2']) else None,
                            'telefono_apoderado1': row['telefono_apoderado1'] if pd.notna(row['telefono_apoderado1']) else None,
                            'telefono_apoderado2': row['telefono_apoderado2'] if pd.notna(row['telefono_apoderado2']) else None,
                            'activo': True
                        }
                    )
                    exitosos += 1
                except Exception as e:
                    errores.append(f'Error en fila {index + 2}: {str(e)}')

            if exitosos > 0:
                messages.success(
                    request, f'Se procesaron {exitosos} estudiantes exitosamente.')
            if errores:
                messages.warning(
                    request, f'Hubo {len(errores)} errores durante la carga.')
                for error in errores:
                    messages.error(request, error)

        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {str(e)}')

        return redirect('estudiantes:list')

    return render(request, 'estudiantes/carga_masiva.html')


@login_required
def descargar_formato(request):
    if not request.user.is_superuser and request.user.perfil.tipo_usuario != 'admin_colegio':
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('estudiantes:list')

    # Obtener los cursos disponibles
    if request.user.is_superuser:
        cursos = Curso.objects.filter(activo=True)
    else:
        cursos = Curso.objects.filter(
            colegio=request.user.perfil.colegio, activo=True)

    # Crear un DataFrame con las columnas requeridas
    df = pd.DataFrame(columns=[
        'nombre',
        'rut',
        'curso',
        'email_estudiante',
        'email_apoderado1',
        'email_apoderado2',
        'telefono_apoderado1',
        'telefono_apoderado2'
    ])

    # Agregar una fila de ejemplo
    df.loc[0] = [
        'Juan Pérez',
        '12345678-9',
        cursos.first().nombre if cursos.exists() else '1°A',
        'juan.perez@email.com',
        'apoderado1@email.com',
        'apoderado2@email.com',
        '+56912345678',
        '+56987654321'
    ]

    # Crear el archivo Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=formato_estudiantes.xlsx'

    # Crear el archivo Excel con dos hojas
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Formato', index=False)

        # Crear hoja de cursos disponibles
        cursos_df = pd.DataFrame(
            list(cursos.values('nombre', 'colegio__nombre')))
        if not cursos_df.empty:
            cursos_df.columns = ['Nombre del Curso', 'Colegio']
            cursos_df.to_excel(
                writer, sheet_name='Cursos Disponibles', index=False)

    return response


