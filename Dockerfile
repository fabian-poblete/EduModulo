# Usa una imagen oficial de Python
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Instala dependencias del sistema (como build tools y libpq para PostgreSQL)
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

# Crea el directorio para archivos estáticos
RUN mkdir -p staticfiles

# Recolecta archivos estáticos
RUN python manage.py collectstatic --noinput --clear

# Expone el puerto en que correrá la app
EXPOSE 8000

# Usa Gunicorn como servidor WSGI
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
