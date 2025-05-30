from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import Mensaje
from usuarios.models import Perfil
from .forms import MensajeForm
from django.utils import timezone

# Create your views here.


@login_required
def lista_mensajes(request):
    perfil = request.user.perfil
    mensajes_recibidos = Mensaje.objects.filter(destinatario=perfil)
    mensajes_enviados = Mensaje.objects.filter(remitente=perfil)

    # Filtrar por estado de lectura
    estado = request.GET.get('estado')
    if estado == 'no_leidos':
        mensajes_recibidos = mensajes_recibidos.filter(leido=False)
    elif estado == 'leidos':
        mensajes_recibidos = mensajes_recibidos.filter(leido=True)

    # Filtrar por prioridad
    prioridad = request.GET.get('prioridad')
    if prioridad:
        mensajes_recibidos = mensajes_recibidos.filter(prioridad=prioridad)
        mensajes_enviados = mensajes_enviados.filter(prioridad=prioridad)

    # Buscar mensajes
    busqueda = request.GET.get('q')
    if busqueda:
        mensajes_recibidos = mensajes_recibidos.filter(
            Q(asunto__icontains=busqueda) |
            Q(contenido__icontains=busqueda) |
            Q(remitente__user__first_name__icontains=busqueda) |
            Q(remitente__user__last_name__icontains=busqueda)
        )
        mensajes_enviados = mensajes_enviados.filter(
            Q(asunto__icontains=busqueda) |
            Q(contenido__icontains=busqueda) |
            Q(destinatario__user__first_name__icontains=busqueda) |
            Q(destinatario__user__last_name__icontains=busqueda)
        )

    # Contar mensajes no leídos
    no_leidos = mensajes_recibidos.filter(leido=False).count()

    return render(request, 'comunicaciones/lista_mensajes.html', {
        'mensajes_recibidos': mensajes_recibidos,
        'mensajes_enviados': mensajes_enviados,
        'no_leidos': no_leidos,
        'estado': estado,
        'prioridad': prioridad,
        'busqueda': busqueda
    })


@login_required
def enviar_mensaje(request):
    perfil = request.user.perfil

    if request.method == 'POST':
        form = MensajeForm(request.POST, user=request.user)
        if form.is_valid():
            # Verificar si ya existe un mensaje idéntico en los últimos 5 segundos
            mensaje_reciente = Mensaje.objects.filter(
                remitente=perfil,
                destinatario=form.cleaned_data['destinatario'],
                asunto=form.cleaned_data['asunto'],
                contenido=form.cleaned_data['contenido'],
                fecha_envio__gte=timezone.now() - timezone.timedelta(seconds=5)
            ).first()

            if mensaje_reciente:
                messages.warning(request, 'Este mensaje ya fue enviado.')
                return redirect('comunicaciones:lista_mensajes')

            mensaje = form.save(commit=False)
            mensaje.remitente = perfil
            mensaje.colegio = perfil.colegio
            mensaje.save()
            messages.success(request, 'Mensaje enviado exitosamente.')
            return redirect('comunicaciones:lista_mensajes')
        else:
            messages.error(
                request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = MensajeForm(user=request.user)

    return render(request, 'comunicaciones/enviar_mensaje.html', {
        'form': form
    })


@login_required
def ver_mensaje(request, pk):
    mensaje = get_object_or_404(Mensaje, pk=pk)
    perfil = request.user.perfil

    # Verificar que el usuario tenga permiso para ver el mensaje
    if mensaje.destinatario != perfil and mensaje.remitente != perfil:
        messages.error(request, 'No tienes permiso para ver este mensaje.')
        return redirect('comunicaciones:lista_mensajes')

    # Marcar como leído si el usuario es el destinatario
    if mensaje.destinatario == perfil and not mensaje.leido:
        mensaje.marcar_como_leido()

    return render(request, 'comunicaciones/ver_mensaje.html', {
        'mensaje': mensaje
    })


@login_required
def eliminar_mensaje(request, pk):
    mensaje = get_object_or_404(Mensaje, pk=pk)
    perfil = request.user.perfil

    # Verificar que el usuario tenga permiso para eliminar el mensaje
    if mensaje.destinatario != perfil and mensaje.remitente != perfil:
        messages.error(
            request, 'No tienes permiso para eliminar este mensaje.')
        return redirect('comunicaciones:lista_mensajes')

    if request.method == 'POST':
        mensaje.delete()
        messages.success(request, 'Mensaje eliminado exitosamente.')
        return redirect('comunicaciones:lista_mensajes')

    return render(request, 'comunicaciones/eliminar_mensaje.html', {
        'mensaje': mensaje
    })


@login_required
def responder_mensaje(request, pk):
    mensaje_original = get_object_or_404(Mensaje, pk=pk)
    perfil = request.user.perfil

    # Verificar que el usuario tenga permiso para responder el mensaje
    if mensaje_original.destinatario != perfil and mensaje_original.remitente != perfil:
        messages.error(
            request, 'No tienes permiso para responder este mensaje.')
        return redirect('comunicaciones:lista_mensajes')

    if request.method == 'POST':
        contenido = request.POST.get('contenido')
        if contenido:
            # Verificar si ya existe una respuesta idéntica en los últimos 5 segundos
            respuesta_reciente = Mensaje.objects.filter(
                remitente=perfil,
                destinatario=mensaje_original.remitente if mensaje_original.destinatario == perfil else mensaje_original.destinatario,
                asunto=f"Re: {mensaje_original.asunto}",
                contenido=contenido,
                fecha_envio__gte=timezone.now() - timezone.timedelta(seconds=5)
            ).first()

            if respuesta_reciente:
                messages.warning(request, 'Esta respuesta ya fue enviada.')
                return redirect('comunicaciones:ver_mensaje', pk=mensaje_original.pk)

            # Crear el nuevo mensaje
            nuevo_mensaje = Mensaje.objects.create(
                remitente=perfil,
                destinatario=mensaje_original.remitente if mensaje_original.destinatario == perfil else mensaje_original.destinatario,
                colegio=perfil.colegio,
                asunto=f"Re: {mensaje_original.asunto}",
                contenido=contenido,
                prioridad=mensaje_original.prioridad
            )
            messages.success(request, 'Respuesta enviada exitosamente.')
            return redirect('comunicaciones:ver_mensaje', pk=mensaje_original.pk)
        else:
            messages.error(
                request, 'El contenido del mensaje no puede estar vacío.')

    return redirect('comunicaciones:ver_mensaje', pk=mensaje_original.pk)
