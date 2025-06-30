import os
import requests
import json
from django.core.mail import send_mail
from django.conf import settings
from .models import Notificacion


def enviar_sms(destinations, message, senderId, debug):
    if debug:
        print(
            f'Enter altiriaSms: {destinations}, message: {message}, senderId: {senderId}')

    try:
        # Cargar las credenciales desde las variables de entorno
        baseUrl = os.getenv('ALTIRIA_BASE_URL')
        apiKey = os.getenv('ALTIRIA_API_KEY')
        apiSecret = os.getenv('ALTIRIA_API_SECRET')

        # Validar que las credenciales están correctamente cargadas
        if not baseUrl or not apiKey or not apiSecret:
            raise ValueError(
                "Las credenciales no están configuradas correctamente en el archivo .env")

        destination = destinations.split(",")

        jsonData = {
            'credentials': {'apiKey': apiKey, 'apiSecret': apiSecret},
            'destination': destination,
            'message': {'msg': message}
        }

        headers = {'Content-Type': 'application/json;charset=UTF-8'}
        response = requests.post(
            f'{baseUrl}/sendSms',
            data=json.dumps(jsonData),
            headers=headers,
            timeout=(5, 60)
        )

        if debug:
            print(f'HTTP Status Code: {response.status_code}')
            if response.status_code == 200:
                jsonParsed = response.json()
                status = jsonParsed.get('status', 'N/A')
                print(f'Altiria Status Code: {status}')
                if status == '000':
                    for detail in jsonParsed.get('details', []):
                        print(
                            f"Destino: {detail.get('destination', '')}, Estado: {detail.get('status', '')}")
                else:
                    print(f'Error: {response.text}')
            else:
                print(f'Error: {response.text}')

        return response.text

    except requests.exceptions.Timeout:
        print("Tiempo de conexión o respuesta agotado")
    except Exception as ex:
        print(f"Error interno: {ex}")


def enviar_notificacion(evento, estudiante, colegio, tipo_evento):

    print(evento,estudiante,colegio,tipo_evento)
    # if not colegio.notificaciones_activas:
    #     return
    # mensaje = render_mensaje(tipo_evento, estudiante, evento)
    # canales = []
    # if colegio.canal_notificacion in ['email', 'ambos']:
    #     canales.append('email')
    # if colegio.canal_notificacion in ['sms', 'ambos']:
    #     canales.append('sms')
    # for canal in canales:
    #     if canal == 'email':
    #         estado = enviar_email_apoderado(estudiante, mensaje)
    #     elif canal == 'sms':
    #         estado = enviar_sms_apoderado(estudiante, mensaje)
    #     else:
    #         estado = 'fallida'
    #     Notificacion.objects.create(
    #         colegio=colegio,
    #         estudiante=estudiante,
    #         tipo_evento=tipo_evento,
    #         canal=canal,
    #         estado=estado,
    #         mensaje=mensaje
    #     )


def enviar_email_apoderado(estudiante, mensaje):
    email = getattr(estudiante.apoderado, 'email', None)
    if not email:
        return 'fallida'
    try:
        send_mail(
            'Notificación del sistema',
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return 'enviada'
    except Exception:
        return 'fallida'


def enviar_sms_apoderado(estudiante, mensaje, debug=False):
    telefono = getattr(estudiante.apoderado, 'telefono', None)
    if not telefono:
        return 'fallida'
    senderId = os.getenv('ALTIRIA_SENDER_ID', 'EduModulo')
    try:
        response = enviar_sms(telefono, mensaje, senderId, debug)
        # Puedes analizar la respuesta para determinar si fue exitosa
        if 'status' in response and '000' in response:
            return 'enviada'
        return 'enviada' if 'OK' in response or '000' in response else 'fallida'
    except Exception:
        return 'fallida'


def render_mensaje(tipo_evento, estudiante, evento):
    if tipo_evento == 'atraso':
        return f"Estimado apoderado, se ha registrado un atraso para el estudiante {estudiante} el día {evento.fecha}."
    elif tipo_evento == 'salida':
        return f"Estimado apoderado, se ha registrado una salida para el estudiante {estudiante} el día {evento.fecha}."
    return ""
