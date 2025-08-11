from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from colegios.models import Colegio
from django.contrib.auth.models import User
from cursos.models import Curso
from estudiantes.models import Estudiante
from inventario.models import Articulo
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
        articulos = Articulo.objects.all()
        total_cursos = cursos.count()
        total_estudiantes = estudiantes.count()
        total_usuarios = usuarios.count()
        total_articulos = articulos.count()
        cursos_activos = cursos.filter(activo=True).count()
        estudiantes_activos = estudiantes.filter(activo=True).count()
        articulos_bueno = articulos.filter(estado__nombre='Bueno').count()
        total_atrasos = Atraso.objects.count()
        total_salidas = Salida.objects.count()
        porcentaje_bueno = round(
            (articulos_bueno / total_articulos * 100) if total_articulos > 0 else 0)
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        # Admin de colegio ve datos de su colegio
        colegio = request.user.perfil.colegio
        cursos = Curso.objects.filter(colegio=colegio)
        estudiantes = Estudiante.objects.filter(curso__colegio=colegio)
        usuarios = User.objects.filter(perfil__colegio=colegio, is_active=True)
        articulos = Articulo.objects.filter(colegio=colegio)
        total_cursos = cursos.count()
        total_estudiantes = estudiantes.count()
        total_usuarios = usuarios.count()
        total_articulos = articulos.count()
        cursos_activos = cursos.filter(activo=True).count()
        estudiantes_activos = estudiantes.filter(activo=True).count()
        articulos_bueno = articulos.filter(estado__nombre='Bueno').count()
        total_atrasos = Atraso.objects.filter(
            estudiante__curso__colegio=colegio).count()
        total_salidas = Salida.objects.filter(
            estudiante__curso__colegio=colegio).count()
        porcentaje_bueno = round(
            (articulos_bueno / total_articulos * 100) if total_articulos > 0 else 0)
    elif request.user.perfil.tipo_usuario == 'administrativo':
        # Administrativos ven datos de su colegio (solo lectura)
        colegio = request.user.perfil.colegio
        cursos = Curso.objects.filter(colegio=colegio)
        estudiantes = Estudiante.objects.filter(curso__colegio=colegio)
        usuarios = User.objects.filter(perfil__colegio=colegio, is_active=True)
        articulos = Articulo.objects.filter(colegio=colegio)
        total_cursos = cursos.count()
        total_estudiantes = estudiantes.count()
        total_usuarios = usuarios.count()
        total_articulos = articulos.count()
        cursos_activos = cursos.filter(activo=True).count()
        estudiantes_activos = estudiantes.filter(activo=True).count()
        articulos_bueno = articulos.filter(estado__nombre='Bueno').count()
        total_atrasos = Atraso.objects.filter(
            estudiante__curso__colegio=colegio).count()
        total_salidas = Salida.objects.filter(
            estudiante__curso__colegio=colegio).count()
        porcentaje_bueno = round(
            (articulos_bueno / total_articulos * 100) if total_articulos > 0 else 0)
    elif request.user.perfil.tipo_usuario == 'profesor':
        # Profesores ven datos de su colegio
        colegio = request.user.perfil.colegio
        cursos = Curso.objects.filter(colegio=colegio)
        estudiantes = Estudiante.objects.filter(curso__colegio=colegio)
        articulos = Articulo.objects.filter(colegio=colegio)
        total_cursos = cursos.count()
        total_estudiantes = estudiantes.count()
        total_usuarios = 0
        total_articulos = articulos.count()
        cursos_activos = cursos.filter(activo=True).count()
        estudiantes_activos = estudiantes.filter(activo=True).count()
        articulos_bueno = articulos.filter(estado__nombre='Bueno').count()
        total_atrasos = Atraso.objects.filter(
            estudiante__curso__colegio=colegio).count()
        total_salidas = Salida.objects.filter(
            estudiante__curso__colegio=colegio).count()
        porcentaje_bueno = round(
            (articulos_bueno / total_articulos * 100) if total_articulos > 0 else 0)
    elif request.user.perfil.tipo_usuario == 'porteria':
        # Portería ve datos de su colegio (solo atrasos y salidas)
        colegio = request.user.perfil.colegio
        cursos = Curso.objects.filter(colegio=colegio)
        estudiantes = Estudiante.objects.filter(curso__colegio=colegio)
        articulos = Articulo.objects.filter(colegio=colegio)
        total_cursos = cursos.count()
        total_estudiantes = estudiantes.count()
        total_usuarios = 0
        total_articulos = articulos.count()
        cursos_activos = cursos.filter(activo=True).count()
        estudiantes_activos = estudiantes.filter(activo=True).count()
        articulos_bueno = articulos.filter(estado__nombre='Bueno').count()
        total_atrasos = Atraso.objects.filter(
            estudiante__curso__colegio=colegio).count()
        total_salidas = Salida.objects.filter(
            estudiante__curso__colegio=colegio).count()
        porcentaje_bueno = round(
            (articulos_bueno / total_articulos * 100) if total_articulos > 0 else 0)
    else:
        # Otros usuarios no ven datos
        cursos = Curso.objects.none()
        estudiantes = Estudiante.objects.none()
        articulos = Articulo.objects.none()
        total_cursos = 0
        total_estudiantes = 0
        total_usuarios = 0
        total_articulos = 0
        cursos_activos = 0
        estudiantes_activos = 0
        total_atrasos = 0
        total_salidas = 0
        porcentaje_bueno = 0

    # Obtener los últimos 5 cursos, estudiantes, usuarios y artículos
    ultimos_cursos = cursos.order_by('-fecha_creacion')[:5]
    ultimos_estudiantes = estudiantes.order_by('-fecha_creacion')[:5]
    ultimos_usuarios = usuarios.order_by(
        '-date_joined')[:5] if 'usuarios' in locals() else []
    ultimos_articulos = articulos.order_by('-fecha_adicion')[:5]

    context = {
        'total_cursos': total_cursos,
        'total_estudiantes': total_estudiantes,
        'total_usuarios': total_usuarios,
        'total_articulos': total_articulos,
        'cursos_activos': cursos_activos,
        'estudiantes_activos': estudiantes_activos,
        'porcentaje_bueno': porcentaje_bueno,
        'ultimos_cursos': ultimos_cursos,
        'ultimos_estudiantes': ultimos_estudiantes,
        'ultimos_usuarios': ultimos_usuarios,
        'ultimos_articulos': ultimos_articulos,
        'total_atrasos': total_atrasos,
        'total_salidas': total_salidas,
    }

    return render(request, 'dashboard/index.html', context)
