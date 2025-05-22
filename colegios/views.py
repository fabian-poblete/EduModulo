from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Colegio, Sede
from .forms import ColegioForm, SedeForm

# Create your views here.


@login_required
def colegio_list(request):
    colegios = Colegio.objects.all()
    return render(request, 'colegios/colegio_list.html', {
        'colegios': colegios
    })


@login_required
def colegio_detail(request, slug):
    colegio = get_object_or_404(Colegio, slug=slug)
    sedes = colegio.sedes.all()
    return render(request, 'colegios/colegio_detail.html', {
        'colegio': colegio,
        'sedes': sedes
    })


@login_required
def colegio_create(request):
    if request.method == 'POST':
        form = ColegioForm(request.POST)
        if form.is_valid():
            colegio = form.save()
            messages.success(request, 'Colegio creado exitosamente.')
            return redirect('colegios:detail', slug=colegio.slug)
    else:
        form = ColegioForm()

    return render(request, 'colegios/colegio_form.html', {
        'form': form,
        'title': 'Crear Colegio'
    })


@login_required
def colegio_update(request, slug):
    colegio = get_object_or_404(Colegio, slug=slug)
    if request.method == 'POST':
        form = ColegioForm(request.POST, instance=colegio)
        if form.is_valid():
            colegio = form.save()
            messages.success(request, 'Colegio actualizado exitosamente.')
            return redirect('colegios:detail', slug=colegio.slug)
    else:
        form = ColegioForm(instance=colegio)

    return render(request, 'colegios/colegio_form.html', {
        'form': form,
        'title': 'Editar Colegio'
    })


@login_required
def sede_create(request, colegio_slug):
    colegio = get_object_or_404(Colegio, slug=colegio_slug)
    if request.method == 'POST':
        form = SedeForm(request.POST)
        if form.is_valid():
            sede = form.save(commit=False)
            sede.colegio = colegio
            sede.save()
            messages.success(request, 'Sede creada exitosamente.')
            return redirect('colegios:detail', slug=colegio.slug)
    else:
        form = SedeForm()

    return render(request, 'colegios/sede_form.html', {
        'form': form,
        'colegio': colegio,
        'title': 'Crear Sede'
    })
