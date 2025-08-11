from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from colegios.models import Colegio
from django.contrib.auth.models import User
from cursos.models import Curso
from estudiantes.models import Estudiante
from atrasos.models import Atraso
from salidas.models import Salida

# Create your views here.


@login_required
def index(request):
    # Obtener datos según el tipo de usuario
    if request.user.is_superuser:
        # Superusuarios ven todos los datos
        cursos = Curso.objects.all()
        estudiantes = Estudiante.objects.all()
        usuarios = User.objects.filter(is_active=True)
        total_cursos = cursos.count()
        total_estudiantes = estudiantes.count()
        total_usuarios = usuarios.count()
        cursos_activos = cursos.filter(activo=True).count()
        estudiantes_activos = estudiantes.filter(activo=True).count()
        total_atrasos = Atraso.objects.count()
        total_salidas = Salida.objects.count()
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        # Admin de colegio ve datos de su colegio
        colegio = request.user.perfil.colegio
        cursos = Curso.objects.filter(colegio=colegio)
        estudiantes = Estudiante.objects.filter(curso__colegio=colegio)
        usuarios = User.objects.filter(perfil__colegio=colegio, is_active=True)
        total_cursos = cursos.count()
        total_estudiantes = estudiantes.count()
        total_usuarios = usuarios.count()
        cursos_activos = cursos.filter(activo=True).count()
        estudiantes_activos = estudiantes.filter(activo=True).count()
        total_atrasos = Atraso.objects.filter(
            estudiante__curso__colegio=colegio).count()
        total_salidas = Salida.objects.filter(
            estudiante__curso__colegio=colegio).count()
    elif request.user.perfil.tipo_usuario == 'administrativo':
        # Administrativos ven datos de su colegio (solo lectura)
        colegio = request.user.perfil.colegio
        cursos = Curso.objects.filter(colegio=colegio)
        estudiantes = Estudiante.objects.filter(curso__colegio=colegio)
        usuarios = User.objects.filter(perfil__colegio=colegio, is_active=True)
        total_cursos = cursos.count()
        total_estudiantes = estudiantes.count()
        total_usuarios = usuarios.count()
        cursos_activos = cursos.filter(activo=True).count()
        estudiantes_activos = estudiantes.filter(activo=True).count()
        total_atrasos = Atraso.objects.filter(
            estudiante__curso__colegio=colegio).count()
        total_salidas = Salida.objects.filter(
            estudiante__curso__colegio=colegio).count()
    elif request.user.perfil.tipo_usuario == 'profesor':
        # Profesores ven datos de su colegio
        colegio = request.user.perfil.colegio
        cursos = Curso.objects.filter(colegio=colegio)
        estudiantes = Estudiante.objects.filter(curso__colegio=colegio)
        total_cursos = cursos.count()
        total_estudiantes = estudiantes.count()
        total_usuarios = 0
        cursos_activos = cursos.filter(activo=True).count()
        estudiantes_activos = estudiantes.filter(activo=True).count()
        total_atrasos = Atraso.objects.filter(
            estudiante__curso__colegio=colegio).count()
        total_salidas = Salida.objects.filter(
            estudiante__curso__colegio=colegio).count()
    elif request.user.perfil.tipo_usuario == 'porteria':
        # Portería ve datos de su colegio (solo atrasos y salidas)
        colegio = request.user.perfil.colegio
        cursos = Curso.objects.filter(colegio=colegio)
        estudiantes = Estudiante.objects.filter(curso__colegio=colegio)
        total_cursos = cursos.count()
        total_estudiantes = estudiantes.count()
        total_usuarios = 0
        cursos_activos = cursos.filter(activo=True).count()
        estudiantes_activos = estudiantes.filter(activo=True).count()
        total_atrasos = Atraso.objects.filter(
            estudiante__curso__colegio=colegio).count()
        total_salidas = Salida.objects.filter(
            estudiante__curso__colegio=colegio).count()
    else:
        # Otros usuarios no ven datos
        cursos = Curso.objects.none()
        estudiantes = Estudiante.objects.none()
        total_cursos = 0
        total_estudiantes = 0
        total_usuarios = 0
        cursos_activos = 0
        estudiantes_activos = 0
        total_atrasos = 0
        total_salidas = 0

    # Obtener los últimos 5 cursos, estudiantes y usuarios
    ultimos_cursos = cursos.order_by('-fecha_creacion')[:5]
    ultimos_estudiantes = estudiantes.order_by('-fecha_creacion')[:5]
    ultimos_usuarios = usuarios.order_by(
        '-date_joined')[:5] if 'usuarios' in locals() else []

    context = {
        'total_cursos': total_cursos,
        'total_estudiantes': total_estudiantes,
        'total_usuarios': total_usuarios,
        'cursos_activos': cursos_activos,
        'estudiantes_activos': estudiantes_activos,
        'ultimos_cursos': ultimos_cursos,
        'ultimos_estudiantes': ultimos_estudiantes,
        'ultimos_usuarios': ultimos_usuarios,
        'total_atrasos': total_atrasos,
        'total_salidas': total_salidas,
    }

    return render(request, 'dashboard/index.html', context)
