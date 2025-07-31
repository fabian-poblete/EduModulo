import os
import requests
import json
import urllib.parse
from django.core.mail import send_mail
from django.conf import settings
from .models import Notificacion


def enviar_sms(destinations, message, senderId, debug):
    print(f"🔧 Función enviar_sms iniciada")
    print(f"📱 Destinos: {destinations}")
    print(f"📝 Mensaje: {message}")
    print(f"🏷️ Sender ID: {senderId}")
    print(f"🐛 Debug mode: {debug}")

    try:
        # Cargar las credenciales desde las variables de entorno
        username = os.getenv('LABSMOBILE_USERNAME')
        password = os.getenv('LABSMOBILE_PASSWORD')

        print(f"👤 Username configurado: {'SÍ' if username else 'NO'}")
        print(f"🔑 Password configurado: {'SÍ' if password else 'NO'}")

        # Validar que las credenciales están correctamente cargadas
        if not username or not password:
            print("❌ Credenciales faltantes")
            raise ValueError(
                "Las credenciales de LabsMobile no están configuradas correctamente")

        # Convertir destinations a formato de array si es necesario
        destination_list = destinations.split(",") if isinstance(
            destinations, str) else destinations

        print(f"📋 Lista de destinos procesada: {destination_list}")

        data = {
            'username': username,
            'password': password,
            'msisdn': destination_list,
            'message': message
        }

        print(f"📦 Datos preparados: {data}")

        url = "https://api.labsmobile.com/get/send.php?" + \
            urllib.parse.urlencode(data, doseq=True)

        print(f"🌐 URL completa: {url}")

        print("📡 Enviando petición HTTP...")
        response = requests.get(url, timeout=(5, 60))

        print(f"📊 HTTP Status Code: {response.status_code}")
        print(f"📨 Response Text: {response.text}")

        return response.text

    except requests.exceptions.Timeout:
        print("⏰ Tiempo de conexión o respuesta agotado")
        return "ERROR: Timeout"
    except Exception as ex:
        print(f"💥 Error interno: {ex}")
        return f"ERROR: {ex}"


def enviar_notificacion(evento, estudiante, colegio, tipo_evento):
    print(f"=== INICIANDO NOTIFICACIÓN ===")
    print(f"Evento: {evento}")
    print(f"Estudiante: {estudiante}")
    print(f"Colegio: {colegio}")
    print(f"Tipo evento: {tipo_evento}")

    if not colegio.notificaciones_activas:
        print("❌ Notificaciones desactivadas para este colegio")
        return

    print("✅ Notificaciones activas")
    mensaje = render_mensaje(tipo_evento, estudiante, evento)
    print(f"📝 Mensaje generado: {mensaje}")

    canales = []

    if colegio.canal_notificacion in ['email', 'ambos']:
        canales.append('email')
        print("📧 Canal email agregado")
    if colegio.canal_notificacion in ['sms', 'ambos']:
        canales.append('sms')
        print("📱 Canal SMS agregado")

    print(f"📡 Canales configurados: {canales}")

    for canal in canales:
        print(f"\n--- ENVIANDO POR {canal.upper()} ---")
        if canal == 'email':
            estado = enviar_email_apoderado(estudiante, mensaje)
        elif canal == 'sms':
            estado = enviar_sms_apoderado(estudiante, mensaje)
        else:
            estado = 'fallida'

        print(f"📊 Estado del envío: {estado}")

        Notificacion.objects.create(
            colegio=colegio,
            estudiante=estudiante,
            tipo_evento=tipo_evento,
            canal=canal,
            estado=estado,
            mensaje=mensaje
        )
        print(f"💾 Notificación guardada en BD")

    print("=== FIN NOTIFICACIÓN ===\n")


def enviar_email_apoderado(estudiante, mensaje):
    print(f"📧 Iniciando envío EMAIL para estudiante: {estudiante}")

    # Intentar usar el email del primer apoderado, si no existe usar el segundo
    print(f"📧 Email apoderado1: {estudiante.email_apoderado1}")
    print(f"📧 Email apoderado2: {estudiante.email_apoderado2}")

    email = estudiante.email_apoderado1 or estudiante.email_apoderado2
    print(f"📧 Email seleccionado: {email}")

    if not email:
        print("❌ No hay email disponible para enviar")
        return 'fallida'

    print(f"📝 Mensaje a enviar: {mensaje}")
    print(f"📧 Email de origen: {settings.DEFAULT_FROM_EMAIL}")

    try:
        print("🚀 Enviando email...")
        send_mail(
            'Notificación del sistema',
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        print("✅ Email enviado exitosamente")
        return 'enviada'
    except Exception as e:
        print(f"💥 Error al enviar email: {e}")
        return 'fallida'


def enviar_sms_apoderado(estudiante, mensaje, debug=False):
    print(f"📱 Iniciando envío SMS para estudiante: {estudiante}")

    # Intentar usar el teléfono del primer apoderado, si no existe usar el segundo
    telefono = estudiante.telefono_apoderado1 or estudiante.telefono_apoderado2
    print(f"📞 Teléfono apoderado1: {estudiante.telefono_apoderado1}")
    print(f"📞 Teléfono apoderado2: {estudiante.telefono_apoderado2}")
    print(f"📞 Teléfono seleccionado: {telefono}")

    if not telefono:
        print("❌ No hay teléfono disponible para enviar SMS")
        return 'fallida'

    senderId = os.getenv('LABSMOBILE_SENDER_ID', 'EduModulo')
    print(f"🏷️ Sender ID: {senderId}")
    print(f"📝 Mensaje a enviar: {mensaje}")

    try:
        print("🚀 Llamando a función enviar_sms...")
        response = enviar_sms(telefono, mensaje, senderId, debug)
        print(f"📨 Respuesta del servicio SMS: {response}")

        # Puedes analizar la respuesta para determinar si fue exitosa
        if 'status' in response and '000' in response:
            print("✅ SMS enviado exitosamente (status 000)")
            return 'enviada'

        if 'OK' in response or '000' in response:
            print("✅ SMS enviado exitosamente")
            return 'enviada'
        else:
            print("❌ SMS falló")
            return 'fallida'
    except Exception as e:
        print(f"💥 Error al enviar SMS: {e}")
        return 'fallida'


def render_mensaje(tipo_evento, estudiante, evento):
    if tipo_evento == 'atraso':
        return f"Estimado apoderado, se ha registrado un atraso para el estudiante {estudiante} el día {evento.fecha}."
    elif tipo_evento == 'salida':
        return f"Estimado apoderado, se ha registrado una salida para el estudiante {estudiante} el día {evento.fecha}."
    return ""
