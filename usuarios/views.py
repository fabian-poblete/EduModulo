from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Perfil
from .forms import UserForm, PerfilForm


@login_required
def usuario_list(request):
    usuarios = User.objects.all()
    return render(request, 'usuarios/usuario_list.html', {
        'usuarios': usuarios
    })


@login_required
def usuario_detail(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    perfil = usuario.perfil
    return render(request, 'usuarios/usuario_detail.html', {
        'usuario': usuario,
        'perfil': perfil
    })


@login_required
def usuario_create(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        perfil_form = PerfilForm(request.POST, request.FILES)
        if user_form.is_valid() and perfil_form.is_valid():
            user = user_form.save()
            perfil = perfil_form.save(commit=False)
            perfil.usuario = user
            perfil.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('usuarios:detail', pk=user.pk)
    else:
        user_form = UserForm()
        perfil_form = PerfilForm()

    return render(request, 'usuarios/usuario_form.html', {
        'user_form': user_form,
        'perfil_form': perfil_form,
        'title': 'Crear Usuario'
    })


@login_required
def usuario_update(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    perfil = usuario.perfil
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=usuario)
        perfil_form = PerfilForm(request.POST, request.FILES, instance=perfil)
        if user_form.is_valid() and perfil_form.is_valid():
            user = user_form.save()
            perfil_form.save()
            messages.success(request, 'Usuario actualizado exitosamente.')
            return redirect('usuarios:detail', pk=user.pk)
    else:
        user_form = UserForm(instance=usuario)
        perfil_form = PerfilForm(instance=perfil)

    return render(request, 'usuarios/usuario_form.html', {
        'user_form': user_form,
        'perfil_form': perfil_form,
        'title': 'Editar Usuario'
    })


@login_required
def profile(request):
    usuario = request.user
    perfil = usuario.perfil
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=usuario)
        perfil_form = PerfilForm(request.POST, request.FILES, instance=perfil)
        if user_form.is_valid() and perfil_form.is_valid():
            user = user_form.save()
            perfil_form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('usuarios:profile')
    else:
        user_form = UserForm(instance=usuario)
        perfil_form = PerfilForm(instance=perfil)

    return render(request, 'usuarios/profile.html', {
        'user_form': user_form,
        'perfil_form': perfil_form,
        'title': 'Mi Perfil'
    })
