from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from colegios.models import Colegio, Sede
from django.contrib.auth.models import User

# Create your views here.


@login_required
def index(request):
    """
    Vista principal del dashboard.
    Muestra un resumen de la información más relevante del sistema.
    """
    context = {
        'title': 'Dashboard',
        'colegios_count': Colegio.objects.count(),
        'usuarios_count': User.objects.count(),
        'sedes_count': Sede.objects.count(),
    }
    return render(request, 'dashboard/index.html', context)
