from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Mensaje
from usuarios.models import Perfil
from .forms import MensajeForm

# Create your views here.


@login_required
def lista_mensajes(request):
    perfil = request.user.perfil
    mensajes_recibidos = Mensaje.objects.filter(destinatario=perfil)
    mensajes_enviados = Mensaje.objects.filter(remitente=perfil)
    return render(request, 'comunicaciones/lista_mensajes.html', {
        'mensajes_recibidos': mensajes_recibidos,
        'mensajes_enviados': mensajes_enviados
    })


@login_required
def enviar_mensaje(request):
    perfil = request.user.perfil
    if request.method == 'POST':
        form = MensajeForm(request.POST)
        if form.is_valid():
            mensaje = form.save(commit=False)
            mensaje.remitente = perfil
            mensaje.colegio = perfil.colegio
            mensaje.save()
            return redirect('comunicaciones:lista_mensajes')
    else:
        form = MensajeForm()
    return render(request, 'comunicaciones/enviar_mensaje.html', {'form': form})
