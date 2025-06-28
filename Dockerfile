FROM python:3.11-slim

# Metadatos
LABEL maintainer="UV Alert Vitoria"
LABEL description="Monitor de radiación UV para Vitoria-Gasteiz con alertas Telegram"
LABEL version="1.0.0"

# Variables de entorno por defecto
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Madrid
ENV UV_THRESHOLD=6
ENV SKIN_TYPE=2
ENV CHECK_INTERVAL_MINUTES=30
ENV EUSKALMET_API_EMAIL=your-email@example.com

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY uv_monitor.py .
COPY openweather_api.py .

# Crear directorio para logs
RUN mkdir -p /app/logs

# Usuario no root por seguridad
RUN useradd -m -u 1000 uvmonitor && \
    chown -R uvmonitor:uvmonitor /app

USER uvmonitor

# Comando para ejecutar la aplicación
CMD ["python", "uv_monitor.py"]