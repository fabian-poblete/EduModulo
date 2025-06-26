from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Estudiante, Curso
from colegios.models import Colegio
from .forms import EstudianteForm
from django.http import HttpResponse
import pandas as pd
from datetime import datetime
import os
import re
from django.db import models

# Create your views here.


@login_required
def estudiante_list(request):
    # Obtener los cursos disponibles según el tipo de usuario
    if request.user.is_superuser:
        cursos = Curso.objects.filter(activo=True)
        estudiantes = Estudiante.objects.all()
        can_edit = True
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        cursos = Curso.objects.filter(
            colegio=request.user.perfil.colegio, activo=True)
        estudiantes = Estudiante.objects.filter(
            curso__colegio=request.user.perfil.colegio)
        can_edit = True
    elif request.user.perfil.tipo_usuario == 'profesor':
        cursos = Curso.objects.filter(
            colegio=request.user.perfil.colegio, activo=True)
        estudiantes = Estudiante.objects.filter(
            curso__colegio=request.user.perfil.colegio)
        can_edit = False
    else:
        messages.error(request, 'No tienes permiso para ver esta página.')
        return redirect('dashboard:index')

    # Aplicar filtros
    curso_id = request.GET.get('curso')
    estado = request.GET.get('estado')
    busqueda = request.GET.get('busqueda')

    if curso_id:
        estudiantes = estudiantes.filter(curso_id=curso_id)

    if estado is not None:
        estudiantes = estudiantes.filter(activo=estado == '1')

    if busqueda:
        estudiantes = estudiantes.filter(
            models.Q(nombre__icontains=busqueda) |
            models.Q(rut__icontains=busqueda)
        )

    return render(request, 'estudiantes/estudiante_list.html', {
        'estudiantes': estudiantes,
        'cursos': cursos,
        'can_edit': can_edit,
        'is_admin': request.user.is_superuser or request.user.perfil.tipo_usuario in ['admin_colegio', 'soporte'],
        'curso_id': curso_id,
        'estado': estado,
        'busqueda': busqueda
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
    Valida el RUT chileno y retorna el RUT sin formato si es válido.
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
        # Retornar RUT sin formato
        return rut
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
            cursos_creados = set()

            for index, row in df.iterrows():
                try:
                    # Validar RUT
                    rut = str(row['rut']).strip()
                    rut_validado = validar_rut(rut)
                    if not rut_validado:
                        raise Exception(f'RUT inválido: {rut}')

                    # Verificar si el estudiante ya existe
                    if Estudiante.objects.filter(rut=rut_validado).exists():
                        raise Exception(
                            f'El estudiante con RUT {rut_validado} ya existe')

                    # Buscar o crear el curso
                    curso_nombre = str(row['curso']).strip()
                    if colegio:
                        curso, creado = Curso.objects.get_or_create(
                            nombre=curso_nombre,
                            colegio=colegio,
                            defaults={'activo': True}
                        )
                    else:
                        # Si es superusuario, necesita especificar el colegio
                        if 'colegio' not in df.columns:
                            raise Exception(
                                'Para superusuarios, el archivo debe incluir la columna "colegio"')
                        colegio_nombre = str(row['colegio']).strip()
                        colegio_obj = Colegio.objects.filter(
                            nombre=colegio_nombre).first()
                        if not colegio_obj:
                            raise Exception(
                                f'No se encontró el colegio: {colegio_nombre}')
                        curso, creado = Curso.objects.get_or_create(
                            nombre=curso_nombre,
                            colegio=colegio_obj,
                            defaults={'activo': True}
                        )

                    if creado:
                        cursos_creados.add(curso_nombre)

                    # Crear estudiante
                    estudiante = Estudiante.objects.create(
                        nombre=row['nombre'],
                        rut=rut_validado,
                        curso=curso,
                        email_estudiante=row['email_estudiante'] if pd.notna(
                            row['email_estudiante']) else None,
                        email_apoderado1=row['email_apoderado1'] if pd.notna(
                            row['email_apoderado1']) else None,
                        email_apoderado2=row['email_apoderado2'] if pd.notna(
                            row['email_apoderado2']) else None,
                        telefono_apoderado1=row['telefono_apoderado1'] if pd.notna(
                            row['telefono_apoderado1']) else None,
                        telefono_apoderado2=row['telefono_apoderado2'] if pd.notna(
                            row['telefono_apoderado2']) else None,
                        activo=True
                    )
                    exitosos += 1
                except Exception as e:
                    errores.append(f'Error en fila {index + 2}: {str(e)}')

            if exitosos > 0:
                messages.success(
                    request, f'Se procesaron {exitosos} estudiantes exitosamente.')
            if cursos_creados:
                messages.info(
                    request, f'Se crearon {len(cursos_creados)} cursos nuevos: {", ".join(cursos_creados)}')
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
def edicion_masiva(request):
    if not request.user.is_superuser and request.user.perfil.tipo_usuario != 'admin_colegio':
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('estudiantes:list')

    if request.method == 'POST':
        if 'archivo' not in request.FILES:
            messages.error(request, 'No se ha seleccionado ningún archivo.')
            return redirect('estudiantes:edicion_masiva')

        archivo = request.FILES['archivo']
        if not archivo.name.endswith('.xlsx'):
            messages.error(request, 'El archivo debe ser un Excel (.xlsx)')
            return redirect('estudiantes:edicion_masiva')

        try:
            # Leer el archivo Excel
            df = pd.read_excel(archivo)

            # Validar columnas requeridas
            columnas_requeridas = ['rut', 'nombre', 'curso', 'email_estudiante',
                                   'email_apoderado1', 'email_apoderado2', 'telefono_apoderado1', 'telefono_apoderado2']
            for col in columnas_requeridas:
                if col not in df.columns:
                    messages.error(
                        request, f'El archivo debe contener la columna: {col}')
                    return redirect('estudiantes:edicion_masiva')

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

                    # Buscar el estudiante por RUT
                    estudiante = Estudiante.objects.filter(
                        rut=rut_validado).first()
                    if not estudiante:
                        raise Exception(
                            f'No se encontró el estudiante con RUT {rut_validado}')

                    # Verificar permisos
                    if not request.user.is_superuser and estudiante.curso.colegio != colegio:
                        raise Exception(
                            f'No tienes permiso para editar este estudiante')

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

                    # Actualizar estudiante
                    estudiante.nombre = row['nombre']
                    estudiante.curso = curso
                    estudiante.email_estudiante = row['email_estudiante'] if pd.notna(
                        row['email_estudiante']) else None
                    estudiante.email_apoderado1 = row['email_apoderado1'] if pd.notna(
                        row['email_apoderado1']) else None
                    estudiante.email_apoderado2 = row['email_apoderado2'] if pd.notna(
                        row['email_apoderado2']) else None
                    estudiante.telefono_apoderado1 = row['telefono_apoderado1'] if pd.notna(
                        row['telefono_apoderado1']) else None
                    estudiante.telefono_apoderado2 = row['telefono_apoderado2'] if pd.notna(
                        row['telefono_apoderado2']) else None
                    estudiante.save()
                    exitosos += 1
                except Exception as e:
                    errores.append(f'Error en fila {index + 2}: {str(e)}')

            if exitosos > 0:
                messages.success(
                    request, f'Se actualizaron {exitosos} estudiantes exitosamente.')
            if errores:
                messages.warning(
                    request, f'Hubo {len(errores)} errores durante la actualización.')
                for error in errores:
                    messages.error(request, error)

        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {str(e)}')

        return redirect('estudiantes:list')

    return render(request, 'estudiantes/edicion_masiva.html')


@login_required
def descargar_estudiantes(request):
    if not request.user.is_superuser and request.user.perfil.tipo_usuario != 'admin_colegio':
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('estudiantes:list')

    # Obtener los estudiantes según el tipo de usuario
    if request.user.is_superuser:
        estudiantes = Estudiante.objects.all()
    else:
        estudiantes = Estudiante.objects.filter(
            curso__colegio=request.user.perfil.colegio)

    # Crear DataFrame con los datos
    data = []
    for estudiante in estudiantes:
        data.append({
            'nombre': estudiante.nombre,
            'rut': estudiante.formatear_rut(),
            'curso': estudiante.curso.nombre,
            'email_estudiante': estudiante.email_estudiante or '',
            'email_apoderado1': estudiante.email_apoderado1 or '',
            'email_apoderado2': estudiante.email_apoderado2 or '',
            'telefono_apoderado1': estudiante.telefono_apoderado1 or '',
            'telefono_apoderado2': estudiante.telefono_apoderado2 or '',
        })

    df = pd.DataFrame(data)

    # Crear respuesta HTTP con el archivo Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=estudiantes.xlsx'

    # Crear el archivo Excel con dos hojas
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Estudiantes', index=False)

        # Crear hoja de instrucciones
        instrucciones = pd.DataFrame({
            'Instrucciones': [
                '1. No modifique la columna RUT, ya que es el identificador único del estudiante',
                '2. El RUT debe ser válido según el algoritmo chileno',
                '3. El curso debe existir en el sistema',
                '4. Los emails son opcionales pero deben ser válidos',
                '5. Los teléfonos son opcionales',
                '6. Guarde el archivo y súbalo en la sección de Edición Masiva'
            ]
        })
        instrucciones.to_excel(writer, sheet_name='Instrucciones', index=False)

    return response


@login_required
def descargar_formato(request):
    if not request.user.is_superuser and request.user.perfil.tipo_usuario != 'admin_colegio':
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('estudiantes:list')

    # Obtener los cursos disponibles
    if request.user.is_superuser:
        cursos = Curso.objects.filter(activo=True)
        colegios = Colegio.objects.filter(activo=True)
    else:
        cursos = Curso.objects.filter(
            colegio=request.user.perfil.colegio, activo=True)
        colegios = [request.user.perfil.colegio]

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

    # Si es superusuario, agregar columna de colegio
    if request.user.is_superuser:
        df['colegio'] = None

    # Agregar una fila de ejemplo
    ejemplo = {
        'nombre': 'Juan Pérez',
        'rut': '123456789',  # Ejemplo de RUT formateado
        'curso': cursos.first().nombre if cursos.exists() else '1°A',
        'email_estudiante': 'juan.perez@email.com',
        'email_apoderado1': 'apoderado1@email.com',
        'email_apoderado2': 'apoderado2@email.com',
        'telefono_apoderado1': '56912345678',
        'telefono_apoderado2': '56987654321'
    }
    if request.user.is_superuser:
        ejemplo['colegio'] = colegios.first(
        ).nombre if colegios.exists() else 'Colegio Ejemplo'
    df.loc[0] = ejemplo

    # Crear el archivo Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=formato_estudiantes.xlsx'

    # Crear el archivo Excel con dos hojas
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Formato', index=False)

       # Crear hoja de instrucciones
        instrucciones = pd.DataFrame({
            'Instrucciones': [
                '1. El RUT debe ser válido según el algoritmo chileno',
                '2. El RUT debe ingresarse sin puntos ni guion (ej: 123456789)',
                '3. Los cursos se crearán automáticamente si no existen',
                '4. Los emails son opcionales pero deben ser válidos',
                '5. Los teléfonos son opcionales',
                '6. No se pueden cargar estudiantes con RUT duplicado'
            ]
        })

        instrucciones.to_excel(writer, sheet_name='Instrucciones', index=False)

    return response


@login_required
def estudiante_toggle_active(request, pk):
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
            request, 'No tienes permiso para cambiar el estado de este estudiante.')
        return redirect('estudiantes:list')

    estudiante.activo = not estudiante.activo
    estudiante.save()
    if estudiante.activo:
        messages.success(
            request, f'El estudiante {estudiante.nombre} ha sido activado.')
    else:
        messages.success(
            request, f'El estudiante {estudiante.nombre} ha sido desactivado.')
    return redirect('estudiantes:list')
