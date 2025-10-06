import os
import re
import requests
import json
import urllib.parse
from django.core.mail import send_mail
from django.conf import settings
from .models import Notificacion


def enviar_sms(destinations, message, senderId, debug):
    try:
        # Cargar las credenciales desde las variables de entorno
        username = os.getenv('LABSMOBILE_USERNAME')
        password = os.getenv('LABSMOBILE_PASSWORD')

        # Validar que las credenciales están correctamente cargadas
        if not username or not password:
            raise ValueError(
                "Las credenciales de LabsMobile no están configuradas correctamente")

        # Convertir destinations a formato de array si es necesario
        destination_list = destinations.split(",") if isinstance(
            destinations, str) else destinations

        data = {
            'username': username,
            'password': password,
            'msisdn': destination_list,
            'message': message
        }

        url = "https://api.labsmobile.com/get/send.php?" + \
            urllib.parse.urlencode(data, doseq=True)

        response = requests.get(url, timeout=(5, 60))
        return response.text

    except requests.exceptions.Timeout:
        return "ERROR: Timeout"
    except Exception as ex:
        return f"ERROR: {ex}"


def enviar_notificacion(evento, estudiante, colegio, tipo_evento):
    if not colegio.notificaciones_activas:
        return

    mensaje = render_mensaje(tipo_evento, estudiante, evento)
    canales = []

    if colegio.canal_notificacion in ['email', 'ambos']:
        canales.append('email')
    if colegio.canal_notificacion in ['sms', 'ambos']:
        canales.append('sms')

    for canal in canales:
        if canal == 'email':
            estado = enviar_email_apoderado(estudiante, mensaje)
        elif canal == 'sms':
            estado = enviar_sms_apoderado(estudiante, mensaje)
        else:
            estado = 'fallida'

        try:
            Notificacion.objects.create(
                colegio=colegio,
                estudiante=estudiante,
                tipo_evento=tipo_evento,
                canal=canal,
                estado=estado,
                mensaje=mensaje
            )
        except Exception as e:
            pass


def enviar_email_apoderado(estudiante, mensaje):
    email = estudiante.email_apoderado1 or estudiante.email_apoderado2

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
    except Exception as e:
        return 'fallida'


def limpiar_telefono_sms(telefono):
    """Limpiar formato de teléfono para SMS con LabsMobile"""
    if not telefono:
        return None

    # Convertir a string y limpiar
    telefono_str = str(telefono).strip()

    # Remover decimales (.0)
    if telefono_str.endswith('.0'):
        telefono_str = telefono_str[:-2]

    # Remover puntos y espacios
    telefono_str = re.sub(r'[.\s]', '', telefono_str)

    # Asegurar que tenga código de país para Chile
    if telefono_str.startswith('9') and len(telefono_str) == 9:
        telefono_str = '56' + telefono_str
    elif telefono_str.startswith('56') and len(telefono_str) == 11:
        pass  # Ya tiene código de país
    else:
        return None  # Formato inválido

    # Agregar corchetes para LabsMobile
    resultado = f"[+{telefono_str}]"
    return resultado


def enviar_sms_apoderado(estudiante, mensaje, debug=False):
    telefono = estudiante.telefono_apoderado1 or estudiante.telefono_apoderado2

    if not telefono:
        return 'fallida'

    # Limpiar formato del teléfono
    telefono_limpio = limpiar_telefono_sms(telefono)
    if not telefono_limpio:
        return 'fallida'

    senderId = os.getenv('LABSMOBILE_SENDER_ID', 'EduModulo')

    try:
        response = enviar_sms(telefono_limpio, mensaje, senderId, debug)

        # Analizar respuesta XML de LabsMobile
        if 'code' in response and '0' in response:
            return 'enviada'
        elif 'status' in response and '000' in response:
            return 'enviada'
        elif 'OK' in response:
            return 'enviada'
        else:
            return 'fallida'
    except Exception as e:
        return 'fallida'


def render_mensaje(tipo_evento, estudiante, evento):
    if tipo_evento == 'atraso':
        # Obtener el nombre del curso
        curso_nombre = estudiante.curso.nombre if estudiante.curso else "N/A"

        # Formatear la fecha de hoy
        fecha_hoy = evento.fecha.strftime('%d/%m/%Y')

        # Formatear la hora
        hora = evento.hora.strftime('%H:%M')

        # Determinar si está justificado
        if evento.justificado:
            return f"Estimado/a, se registró un atraso justificado para {estudiante.nombre} hoy a las {hora}"
        else:
            return f"Estimado/a, se registró un atraso sin justificar para {estudiante.nombre} hoy a las {hora}"

    elif tipo_evento == 'salida':
        # Formatear la fecha
        fecha = evento.fecha.strftime('%d/%m/%Y')

        # Formatear la hora
        hora = evento.hora.strftime('%H:%M')

        return f"Estimado/a, se registró una salida para {estudiante.nombre} hoy a las {hora}"
    return ""
