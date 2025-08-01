from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Curso
from .forms import CursoForm

# Create your views here.


@login_required
def curso_list(request):
    # Superusuarios ven todos los cursos
    if request.user.is_superuser:
        cursos = Curso.objects.all()
        can_edit = True
    # Admin de colegio ve cursos de su colegio
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        cursos = Curso.objects.filter(colegio=request.user.perfil.colegio)
        can_edit = True
    # Profesores ven cursos de su colegio pero no pueden editar
    elif request.user.perfil.tipo_usuario == 'profesor':
        cursos = Curso.objects.filter(colegio=request.user.perfil.colegio)
        can_edit = False
    else:
        messages.error(request, 'No tienes permiso para ver esta página.')
        return redirect('dashboard:index')

    return render(request, 'cursos/curso_list.html', {
        'cursos': cursos,
        'can_edit': can_edit
    })


@login_required
def curso_create(request, colegio_id=None):
    # Verificar permisos
    if not (request.user.is_superuser or request.user.perfil.tipo_usuario == 'admin_colegio'):
        messages.error(request, 'No tienes permiso para crear cursos.')
        return redirect('cursos:list')

    if request.method == 'POST':
        form = CursoForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                curso = form.save()
                messages.success(request, 'Curso creado exitosamente.')
                return redirect('cursos:list')
            except Exception as e:
                messages.error(request, f'Error al crear el curso: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        form = CursoForm(user=request.user)

    return render(request, 'cursos/curso_form.html', {
        'form': form,
        'title': 'Crear Curso'
    })


@login_required
def curso_update(request, pk):
    curso = get_object_or_404(Curso, pk=pk)

    # Verificar permisos
    if request.user.is_superuser:
        can_edit = True
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        can_edit = curso.colegio == request.user.perfil.colegio
    else:
        can_edit = False

    if not can_edit:
        messages.error(request, 'No tienes permiso para editar este curso.')
        return redirect('cursos:list')

    if request.method == 'POST':
        form = CursoForm(request.POST, instance=curso, user=request.user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Curso actualizado exitosamente.')
                return redirect('cursos:list')
            except Exception as e:
                messages.error(
                    request, f'Error al actualizar el curso: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        form = CursoForm(instance=curso, user=request.user)

    return render(request, 'cursos/curso_form.html', {
        'form': form,
        'title': 'Editar Curso',
        'is_edit': True
    })


@login_required
def curso_delete(request, pk):
    curso = get_object_or_404(Curso, pk=pk)

    # Verificar permisos
    if request.user.is_superuser:
        can_delete = True
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        can_delete = curso.colegio == request.user.perfil.colegio
    else:
        can_delete = False

    if not can_delete:
        messages.error(request, 'No tienes permiso para eliminar este curso.')
        return redirect('cursos:list')

    if request.method == 'POST':
        try:
            curso.delete()
            messages.success(request, 'Curso eliminado exitosamente.')
            return redirect('cursos:list')
        except Exception as e:
            messages.error(request, f'Error al eliminar el curso: {str(e)}')

    return render(request, 'cursos/curso_confirm_delete.html', {
        'curso': curso
    })


@login_required
def curso_detail(request, pk):
    from estudiantes.models import Estudiante
    from atrasos.models import Atraso
    from salidas.models import Salida
    curso = get_object_or_404(Curso, pk=pk)
    estudiantes = Estudiante.objects.filter(curso=curso)
    atrasos = Atraso.objects.filter(estudiante__curso=curso)
    salidas = Salida.objects.filter(estudiante__curso=curso)
    estudiantes_count = estudiantes.count()
    atrasos_count = atrasos.count()
    salidas_count = salidas.count()
    return render(request, 'cursos/curso_detail.html', {
        'curso': curso,
        'colegio': curso.colegio,
        'estudiantes_count': estudiantes_count,
        'atrasos_count': atrasos_count,
        'salidas_count': salidas_count,
        'estudiantes': estudiantes,
        'atrasos': atrasos,
        'salidas': salidas,
    })
