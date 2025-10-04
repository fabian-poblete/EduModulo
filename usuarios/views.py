from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db import transaction
from .models import Perfil
from .forms import UserForm, PerfilForm
from django import forms


def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('login')


@login_required
def usuario_list(request):
    # Superusuarios tienen acceso total
    if request.user.is_superuser:
        usuarios = User.objects.all()
        can_edit = True
        can_delete = True
    # Admin de colegio solo ve usuarios de su colegio
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        usuarios = User.objects.filter(
            perfil__colegio=request.user.perfil.colegio)
        can_edit = True
        can_delete = True

    else:
        messages.error(request, 'No tienes permiso para ver esta página.')
        return redirect('dashboard:index')

    return render(request, 'usuarios/usuario_list.html', {
        'usuarios': usuarios,
        'can_edit': can_edit,
        'can_delete': can_delete
    })


@login_required
def usuario_detail(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    try:
        perfil = usuario.perfil
    except Perfil.DoesNotExist:
        perfil = Perfil.objects.create(user=usuario)

    # Verificar permisos
    if request.user.is_superuser:
        can_edit = True
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        can_edit = perfil.colegio == request.user.perfil.colegio
    else:
        can_edit = False

    if not can_edit:
        messages.error(request, 'No tienes permiso para ver este usuario.')
        return redirect('usuarios:list')

    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES,
                          instance=perfil, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('usuarios:detail', pk=usuario.pk)
    else:
        form = PerfilForm(instance=perfil, user=request.user)

    context = {
        'usuario': usuario,
        'perfil': perfil,
        'form': form,
        'is_superuser': usuario.is_superuser,
    }
    return render(request, 'usuarios/detail.html', context)


@login_required
@transaction.atomic
def usuario_create(request, colegio_id=None):
    # Superusuarios tienen acceso total
    if request.user.is_superuser:
        can_create_any = True
    # Admin de colegio solo puede crear usuarios para su colegio
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        can_create_any = False
    else:
        messages.error(request, 'No tienes permiso para crear usuarios.')
        return redirect('usuarios:list')

    if request.method == 'POST':
        user_form = UserForm(request.POST)
        perfil_form = PerfilForm(request.POST, user=request.user)

        if user_form.is_valid() and perfil_form.is_valid():
            try:
                # Crear el usuario usando el email como username
                user = user_form.save(commit=False)
                user.username = user_form.cleaned_data['email']
                user.set_password(user_form.cleaned_data['password'])
                user.save()

                # Actualizar el perfil existente (creado por la señal post_save)
                perfil = user.perfil
                perfil.tipo_usuario = perfil_form.cleaned_data['tipo_usuario']

                # Si es admin_colegio, forzar el colegio del creador
                if not can_create_any:
                    perfil.colegio = request.user.perfil.colegio
                else:
                    # If a colegio_id was provided in the URL (from quick actions), use that
                    # Otherwise, use the colegio selected in the form by the superuser
                    colegio_a_asignar = colegio_id if colegio_id is not None else perfil_form.cleaned_data[
                        'colegio']
                    perfil.colegio = colegio_a_asignar

                perfil.save()

                messages.success(request, 'Usuario creado exitosamente.')
                return redirect('usuarios:list')
            except Exception as e:
                messages.error(request, f'Error al crear el usuario: {str(e)}')
        else:
            # Mostrar errores específicos de cada formulario
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
            for field, errors in perfil_form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        user_form = UserForm()
        perfil_form = PerfilForm(user=request.user)

    return render(request, 'usuarios/usuario_form.html', {
        'title': 'Crear Usuario',
        'user_form': user_form,
        'perfil_form': perfil_form,
    })


@login_required
def usuario_update(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    perfil = usuario.perfil

    # Verificar permisos
    if request.user.is_superuser:
        can_edit = True
    elif request.user.perfil.tipo_usuario == 'admin_colegio':
        can_edit = perfil.colegio == request.user.perfil.colegio
    else:
        can_edit = False

    if not can_edit:
        messages.error(request, 'No tienes permiso para editar este usuario.')
        return redirect('usuarios:list')

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=usuario)
        perfil_form = PerfilForm(
            request.POST, instance=perfil, user=request.user)

        # Si estamos editando, hacer que los campos de contraseña sean opcionales
        if user_form.is_valid():
            # Verificar si se proporcionó una nueva contraseña
            password = user_form.cleaned_data.get('password')
            confirm_password = user_form.cleaned_data.get('confirm_password')

            # Si se proporcionó una contraseña, verificar que coincida
            if password and password != confirm_password:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, 'usuarios/usuario_form.html', {
                    'user_form': user_form,
                    'perfil_form': perfil_form,
                    'title': 'Editar Usuario',
                    'is_edit': True
                })

            try:
                # Actualizar usuario
                user = user_form.save(commit=False)
                if password:  # Solo actualizar la contraseña si se proporcionó una nueva
                    user.set_password(password)
                user.save()

                # Actualizar perfil
                if perfil_form.is_valid():
                    # Si es admin_colegio, forzar el colegio del editor
                    if request.user.perfil.tipo_usuario == 'admin_colegio':
                        perfil_form.instance.colegio = request.user.perfil.colegio
                    perfil_form.save()
                    messages.success(
                        request, 'Usuario actualizado exitosamente.')
                    return redirect('usuarios:detail', pk=user.pk)
                else:
                    for field, errors in perfil_form.errors.items():
                        for error in errors:
                            messages.error(
                                request, f'Error en {field}: {error}')
            except Exception as e:
                messages.error(
                    request, f'Error al actualizar el usuario: {str(e)}')
        else:
            # Mostrar solo errores relevantes
            for field, errors in user_form.errors.items():
                if field == 'email' and 'already exists' in str(errors):
                    messages.error(
                        request, 'Este correo electrónico ya está registrado')
                elif field not in ['password', 'confirm_password']:
                    for error in errors:
                        messages.error(request, f'Error en {field}: {error}')
    else:
        # Inicializar el formulario con los datos existentes
        user_form = UserForm(instance=usuario)
        # Hacer que los campos de contraseña sean opcionales
        user_form.fields['password'].required = False
        user_form.fields['confirm_password'].required = False
        perfil_form = PerfilForm(instance=perfil, user=request.user)

    return render(request, 'usuarios/usuario_form.html', {
        'user_form': user_form,
        'perfil_form': perfil_form,
        'title': 'Editar Usuario',
        'is_edit': True
    })


@login_required
def usuario_delete(request, pk):
    usuario = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        # Verificar que no sea el usuario actual
        if usuario == request.user:
            messages.error(request, 'No puedes eliminar tu propio usuario.')
            return redirect('usuarios:list')

        # Eliminar el usuario (esto también eliminará el perfil por CASCADE)
        usuario.delete()
        messages.success(request, 'Usuario eliminado exitosamente.')
        return redirect('usuarios:list')

    return render(request, 'usuarios/usuario_confirm_delete.html', {
        'usuario': usuario
    })


@login_required
def profile(request):
    usuario = request.user
    perfil = usuario.perfil

    if request.method == 'POST':
        # Verificar si solo se está cambiando la contraseña
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password and confirm_password:
            # Si se proporcionó una contraseña, validar que coincida
            if password != confirm_password:
                messages.error(request, 'Las contraseñas no coinciden.')
                return redirect('usuarios:profile')

            # Validar longitud mínima de contraseña
            if len(password) < 8:
                messages.error(
                    request, 'La contraseña debe tener al menos 8 caracteres.')
                return redirect('usuarios:profile')

            # Actualizar solo la contraseña
            usuario.set_password(password)
            usuario.save()
            messages.success(request, 'Contraseña actualizada exitosamente.')
            return redirect('usuarios:profile')

        # Si no se está cambiando la contraseña, procesar el formulario normal
        user_form = UserForm(request.POST, instance=usuario)
        perfil_form = PerfilForm(request.POST, request.FILES, instance=perfil)

        if user_form.is_valid() and perfil_form.is_valid():
            try:
                # Actualizar usuario
                user = user_form.save(commit=False)
                user.save()

                # Actualizar perfil
                perfil_form.save()

                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('usuarios:profile')
            except Exception as e:
                messages.error(
                    request, f'Error al actualizar el perfil: {str(e)}')
        else:
            # Mostrar errores específicos de cada formulario
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
            for field, errors in perfil_form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        user_form = UserForm(instance=usuario)
        perfil_form = PerfilForm(instance=perfil)

    return render(request, 'usuarios/profile.html', {
        'user_form': user_form,
        'perfil_form': perfil_form,
        'title': 'Mi Perfil'
    })
