# UV Alert Vitoria-Gasteiz

Sistema de monitoreo de radiación UV para Vitoria-Gasteiz con alertas por Telegram.

## Características

- 🌞 Monitorea el índice UV en tiempo real usando la API de Euskalmet
- 📱 Envía alertas a Telegram cuando el UV supera el umbral configurado
- ⏱️ Calcula el tiempo seguro de exposición según tu tipo de piel
- 💊 Ajusta los cálculos para personas con medicación fotosensibilizante
- 🔄 Verificación automática cada 30 minutos (configurable)
- 🐳 Listo para Docker y Raspberry Pi

## Requisitos Previos

1. **Bot de Telegram**:
   - Habla con [@BotFather](https://t.me/botfather) en Telegram
   - Crea un nuevo bot con `/newbot`
   - Guarda el token que te proporciona

2. **Tu Chat ID de Telegram**:
   - Habla con [@userinfobot](https://t.me/userinfobot)
   - Te dirá tu ID de usuario

3. **Docker instalado** en tu Raspberry Pi
## Instalación

### Opción 1: Usar imagen de Docker Hub

1. Crea un archivo `.env` con tu configuración:
```bash
cp .env.example .env
nano .env
```

2. Ejecuta con docker-compose:
```bash
docker-compose up -d
```

### Opción 2: Construir localmente

1. Clona el repositorio:
```bash
git clone https://github.com/tu-usuario/uv-alert-vitoria.git
cd uv-alert-vitoria
```

2. Construye la imagen:
```bash
docker build -t uv-alert-vitoria .
```

3. Ejecuta el contenedor:
```bash
docker run -d \
  --name uv-alert-vitoria \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN="tu_token" \
  -e TELEGRAM_CHAT_ID="tu_chat_id" \
  -e UV_THRESHOLD=6 \
  -e SKIN_TYPE=2 \
  -v $(pwd)/logs:/app/logs \
  uv-alert-vitoria
```
## Configuración

### Variables de Entorno

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram | Requerido |
| `TELEGRAM_CHAT_ID` | ID del chat donde enviar alertas | Requerido |
| `UV_THRESHOLD` | Índice UV considerado peligroso | 6 |
| `SKIN_TYPE` | Tipo de piel (1-6) | 2 |
| `CHECK_INTERVAL_MINUTES` | Minutos entre verificaciones | 30 |

### Tipos de Piel

1. **Tipo I**: Muy clara - Se quema siempre, nunca se broncea
2. **Tipo II**: Clara - Se quema fácilmente, se broncea mínimamente
3. **Tipo III**: Media - Se quema moderadamente, se broncea gradualmente
4. **Tipo IV**: Morena - Se quema mínimamente, se broncea bien
5. **Tipo V**: Muy morena - Raramente se quema, se broncea profundamente
6. **Tipo VI**: Negra - Nunca se quema

**Nota**: El programa ya ajusta automáticamente los tiempos al 50% debido a la medicación fotosensibilizante.
## Índice UV - Niveles

| Índice UV | Nivel | Emoji | Riesgo |
|-----------|-------|-------|---------|
| 0-2 | Bajo | 🟢 | Mínimo |
| 3-5 | Moderado | 🟡 | Bajo |
| 6-7 | Alto | 🟠 | Moderado |
| 8-10 | Muy Alto | 🔴 | Alto |
| 11+ | Extremo | 🟣 | Muy Alto |

## Logs

Los logs se guardan en el directorio `./logs/uv_monitor.log`

Para ver los logs en tiempo real:
```bash
docker logs -f uv-alert-vitoria
```

## Comandos Útiles

```bash
# Ver estado del contenedor
docker ps

# Detener el servicio
docker-compose down

# Reiniciar el servicio
docker-compose restart

# Ver logs
docker-compose logs -f
```

## Solución de Problemas

1. **No recibo alertas**: Verifica que el token y chat ID sean correctos
2. **Error de conexión**: Asegúrate de que tu Raspberry Pi tenga acceso a Internet
3. **Datos no actualizados**: Verifica los logs para ver si hay errores de la API

## Licencia

MIT