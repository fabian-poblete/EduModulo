from django.shortcuts import render

# Create your views here.


def home(request):
    """
    Vista principal pública del sistema.
    """
    return render(request, 'public/home.html')
