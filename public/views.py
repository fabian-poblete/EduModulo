from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required

# Create your views here.


def home(request):
    """
    Vista principal pública del sistema.
    """
    return render(request, 'public/home.html')


def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        institution = request.POST.get('institution')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Lógica para enviar el correo electrónico
        try:
            send_mail(
                # Asunto del correo
                f'Mensaje de contacto desde EduModulo: {subject}',
                # Cuerpo del correo
                f'Nombre: {name}\nCorreo: {email}\nTeléfono: {phone}\nInstitución: {institution}\nMensaje:\n{message}',
                settings.DEFAULT_FROM_EMAIL,  # Remitente
                ['fepoblete2001@gmail.com'],  # Destinatario
                fail_silently=False,  # Si es True, no levanta error si falla el envío
            )
            return JsonResponse({'success': True, 'message': '¡Mensaje recibido exitosamente! Nos contactaremos contigo pronto.'})
        except Exception as e:
            # En caso de error al enviar el correo
            print(f"Error al enviar el correo: {e}")
            return JsonResponse({'success': False, 'message': 'Ocurrió un error al enviar el mensaje.'}, status=500)

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)


@login_required
def download_view(request):
    return render(request, 'public/descarga.html')
