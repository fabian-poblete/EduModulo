# Usa una imagen oficial de Python
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copia el resto del proyecto
COPY . .

# Crea el directorio para archivos estáticos y establece permisos
RUN mkdir -p staticfiles media && \
    chmod -R 755 staticfiles media

# Recolecta archivos estáticos
RUN python manage.py collectstatic --noinput --clear

# Expone el puerto en que correrá la app
EXPOSE 8000

# Configura variables de entorno
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV APP_NAME=edumodulo

# Usa Gunicorn como servidor WSGI con configuración optimizada
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
