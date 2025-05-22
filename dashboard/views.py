from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from colegios.models import Colegio
from django.contrib.auth.models import User

# Create your views here.


@login_required
def index(request):
    """
    Vista principal del dashboard.
    Muestra un resumen de la información más relevante del sistema.
    """
    colegios_count = Colegio.objects.count()
    usuarios_count = User.objects.count()
    context = {
        'title': 'Dashboard',
        'colegios_count': colegios_count,
        'usuarios_count': usuarios_count,
    }
    return render(request, 'dashboard/index.html', context)
