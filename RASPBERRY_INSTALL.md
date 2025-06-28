# 🍓 Guía de Instalación para Raspberry Pi

Esta guía te ayudará a instalar el sistema UV Alert Vitoria-Gasteiz en tu Raspberry Pi paso a paso.

## 📋 Requisitos Previos

- Raspberry Pi con Raspbian OS
- Conexión a Internet
- Acceso SSH o terminal
- Bot de Telegram configurado

## 🚀 Instalación Paso a Paso

### Paso 1: Instalar Docker (si no lo tienes)

```bash
# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Añadir tu usuario al grupo docker
sudo usermod -aG docker $USER

# Reiniciar para aplicar cambios
sudo reboot
```

### Paso 2: Instalar Docker Compose

```bash
# Instalar pip3 si no lo tienes
sudo apt install python3-pip -y

# Instalar docker-compose
sudo pip3 install docker-compose
```

### Paso 3: Crear directorio para el proyecto

```bash
# Crear directorio
mkdir ~/uv-alert-vitoria
cd ~/uv-alert-vitoria
```

### Paso 4: Crear archivo docker-compose.yml

```bash
nano docker-compose.yml
```

Pega este contenido:

```yaml
version: '3.8'

services:
  uv-monitor:
    image: alexdiazdecerio/uv-alert-vitoria:latest
    container_name: uv-alert-vitoria
    restart: unless-stopped
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
      - UV_THRESHOLD=${UV_THRESHOLD:-6}
      - SKIN_TYPE=${SKIN_TYPE:-3}
      - CHECK_INTERVAL_MINUTES=${CHECK_INTERVAL_MINUTES:-30}
      - TZ=Europe/Madrid
    volumes:
      - ./logs:/app/logs
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Guarda con `Ctrl+X`, luego `Y`, luego `Enter`.

### Paso 5: Crear archivo de configuración

```bash
nano .env
```

Pega y modifica con tus datos:

```env
# Tu token del bot (de @BotFather)
TELEGRAM_BOT_TOKEN=tu_token_aqui

# Tu ID de Telegram (de @userinfobot)
TELEGRAM_CHAT_ID=tu_chat_id_aqui

# Umbral UV peligroso (por defecto 6)
UV_THRESHOLD=6

# Tu tipo de piel (1-6)
SKIN_TYPE=3

# Intervalo de verificación en minutos
CHECK_INTERVAL_MINUTES=30
```

### Paso 6: Iniciar el servicio

```bash
# Descargar la imagen
docker-compose pull

# Iniciar el contenedor
docker-compose up -d

# Verificar que está funcionando
docker ps

# Ver los logs
docker-compose logs -f
```

## 🔧 Comandos Útiles

```bash
# Ver estado
docker ps

# Ver logs en tiempo real
docker-compose logs -f

# Parar el servicio
docker-compose down

# Reiniciar
docker-compose restart

# Actualizar a nueva versión
docker-compose pull
docker-compose up -d
```

## 🔄 Configurar Inicio Automático (Opcional)

Para que se inicie automáticamente al encender la Raspberry Pi:

```bash
# Crear servicio systemd
sudo nano /etc/systemd/system/uv-alert.service
```

Pega este contenido:

```ini
[Unit]
Description=UV Alert Vitoria-Gasteiz
Requires=docker.service
After=docker.service

[Service]
Restart=always
User=pi
Group=docker
WorkingDirectory=/home/pi/uv-alert-vitoria
ExecStartPre=/usr/bin/docker-compose pull
ExecStart=/usr/bin/docker-compose up
ExecStop=/usr/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

Luego:

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar el servicio
sudo systemctl enable uv-alert

# Iniciar el servicio
sudo systemctl start uv-alert

# Ver estado
sudo systemctl status uv-alert
```

## ❓ Solución de Problemas

### No recibo mensajes

1. Verifica que iniciaste conversación con el bot en Telegram
2. Comprueba que el token y chat ID son correctos:
   ```bash
   cat .env
   ```
3. Revisa los logs:
   ```bash
   docker-compose logs --tail 50
   ```

### Error al iniciar Docker

Si ves "permission denied":
```bash
# Asegúrate de estar en el grupo docker
groups

# Si no aparece docker, cierra sesión y vuelve a entrar
logout
```

### El contenedor se reinicia constantemente

Revisa los logs para ver el error:
```bash
docker-compose logs --tail 100
```

## 📊 Verificar que Funciona

Deberías ver en los logs algo como:
```
uv-alert-vitoria | 2024-01-15 10:30:00 - INFO - Iniciando UV Monitor para Vitoria-Gasteiz
uv-alert-vitoria | 2024-01-15 10:30:00 - INFO - Umbral UV: 6
uv-alert-vitoria | 2024-01-15 10:30:00 - INFO - Tipo de piel: 3
uv-alert-vitoria | 2024-01-15 10:30:01 - INFO - Índice UV obtenido: 2.5
uv-alert-vitoria | 2024-01-15 10:30:01 - INFO - UV actual: 2.5 - Bajo 🟢
```

## 🎉 ¡Listo!

Tu Raspberry Pi ahora está monitoreando el UV en Vitoria-Gasteiz y te avisará cuando sea peligroso salir al sol.

## 📱 Mensajes que Recibirás

**Cuando el UV es peligroso:**
```
⚠️ ALERTA UV - Vitoria-Gasteiz ⚠️
🟠 Índice UV: 7 (Alto)
⏱️ Tiempo máximo sin protección: 14 minutos
```

**Cuando vuelve a ser seguro:**
```
✅ UV SEGURO - Vitoria-Gasteiz ✅
🟢 Índice UV: 2 (Bajo)
🌤️ Puedes salir con precauciones normales
```