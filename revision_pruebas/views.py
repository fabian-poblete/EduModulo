from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import RevisionPrueba
from .forms import RevisionPruebaForm
from usuarios.models import Perfil

# Create your views here.


@login_required
def lista_revisiones(request):
    perfil = request.user.perfil
    revisiones = RevisionPrueba.objects.filter(colegio=perfil.colegio)
    return render(request, 'revision_pruebas/lista_revisiones.html', {'revisiones': revisiones})


@login_required
def registrar_revision(request):
    perfil = request.user.perfil
    if request.method == 'POST':
        form = RevisionPruebaForm(request.POST)
        if form.is_valid():
            revision = form.save(commit=False)
            revision.profesor = perfil
            revision.colegio = perfil.colegio
            revision.save()
            return redirect('revision_pruebas:lista_revisiones')
    else:
        form = RevisionPruebaForm()
    return render(request, 'revision_pruebas/registrar_revision.html', {'form': form})
