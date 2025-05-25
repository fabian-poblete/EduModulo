from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import SalidaAnticipada
from .forms import SalidaAnticipadaForm
from usuarios.models import Perfil
from estudiantes.models import Estudiante
from django.http import HttpResponseForbidden


def puede_ver_salidas(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.perfil.tipo_usuario in ['admin_colegio', 'profesor', 'apoderado']


@login_required
@user_passes_test(puede_ver_salidas)
def lista_salidas(request):
    perfil = request.user.perfil
    if perfil.tipo_usuario == 'apoderado':
        # Mostrar solo salidas de estudiantes asociados al apoderado
        estudiantes = Estudiante.objects.filter(
            email_apoderado1=perfil.user.email) | Estudiante.objects.filter(email_apoderado2=perfil.user.email)
        salidas = SalidaAnticipada.objects.filter(estudiante__in=estudiantes)
    else:
        salidas = SalidaAnticipada.objects.filter(colegio=perfil.colegio)
    return render(request, 'salidas/lista_salidas.html', {'salidas': salidas})


@login_required
@user_passes_test(puede_ver_salidas)
def registrar_salida(request):
    perfil = request.user.perfil
    if perfil.tipo_usuario not in ['admin_colegio', 'profesor', 'apoderado']:
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = SalidaAnticipadaForm(request.POST)
        if form.is_valid():
            salida = form.save(commit=False)
            salida.autorizado_por = perfil
            salida.colegio = perfil.colegio
            salida.save()
            return redirect('salidas:lista_salidas')
    else:
        form = SalidaAnticipadaForm()
    return render(request, 'salidas/registrar_salida.html', {'form': form})


@login_required
@user_passes_test(puede_ver_salidas)
def detalle_salida(request, pk):
    salida = get_object_or_404(SalidaAnticipada, pk=pk)
    perfil = request.user.perfil
    # Permitir ver solo si es admin_colegio, profesor del colegio, o apoderado del estudiante
    if perfil.tipo_usuario == 'apoderado':
        if salida.estudiante.email_apoderado1 != perfil.user.email and salida.estudiante.email_apoderado2 != perfil.user.email:
            return HttpResponseForbidden()
    elif perfil.tipo_usuario in ['profesor', 'admin_colegio']:
        if salida.colegio != perfil.colegio:
            return HttpResponseForbidden()
    return render(request, 'salidas/detalle_salida.html', {'salida': salida})
