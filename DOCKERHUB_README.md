# UV Alert Vitoria-Gasteiz 🌞

[![Docker Pulls](https://img.shields.io/docker/pulls/alexdiazdecerio/uv-alert-vitoria)](https://hub.docker.com/r/alexdiazdecerio/uv-alert-vitoria)
[![Docker Image Size](https://img.shields.io/docker/image-size/alexdiazdecerio/uv-alert-vitoria)](https://hub.docker.com/r/alexdiazdecerio/uv-alert-vitoria)

Sistema de monitoreo de radiación UV en tiempo real para Vitoria-Gasteiz con alertas automáticas por Telegram.

## 🎯 Características

- 📊 Monitorea el índice UV usando la API de Euskalmet
- 📱 Envía alertas a Telegram cuando el UV es peligroso
- ⏱️ Calcula tiempo seguro de exposición según tu tipo de piel
- 💊 Ajuste especial para medicación fotosensibilizante (50% reducción)
- 🔄 Verificación automática configurable
- 🐳 Optimizado para Raspberry Pi y ARM

## 🚀 Inicio Rápido

```bash
docker run -d \
  --name uv-alert \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN="tu_token" \
  -e TELEGRAM_CHAT_ID="tu_chat_id" \
  -e UV_THRESHOLD=6 \
  -e SKIN_TYPE=3 \
  alexdiazdecerio/uv-alert-vitoria:latest
```

## 📋 Requisitos Previos

1. **Bot de Telegram**: Crear uno con [@BotFather](https://t.me/botfather)
2. **Chat ID**: Obtener con [@userinfobot](https://t.me/userinfobot)
3. **Docker** instalado

## ⚙️ Variables de Entorno

| Variable | Descripción | Por defecto | Requerido |
|----------|-------------|-------------|-----------|
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram | - | ✅ |
| `TELEGRAM_CHAT_ID` | ID del chat para alertas | - | ✅ |
| `UV_THRESHOLD` | Índice UV considerado peligroso | 6 | ❌ |
| `SKIN_TYPE` | Tipo de piel (1-6) | 2 | ❌ |
| `CHECK_INTERVAL_MINUTES` | Minutos entre verificaciones | 30 | ❌ |

### Tipos de Piel

1. **Muy clara**: Se quema siempre, nunca se broncea
2. **Clara**: Se quema fácilmente, se broncea mínimamente  
3. **Media**: Se quema moderadamente, se broncea gradualmente
4. **Morena**: Se quema mínimamente, se broncea bien
5. **Muy morena**: Raramente se quema, se broncea profundamente
6. **Negra**: Nunca se quema

## 🐳 Docker Compose

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
      - UV_THRESHOLD=6
      - SKIN_TYPE=3
      - CHECK_INTERVAL_MINUTES=30
    volumes:
      - ./logs:/app/logs
```

## 📊 Niveles UV

| Índice | Nivel | Riesgo | Emoji |
|--------|-------|--------|-------|
| 0-2 | Bajo | Mínimo | 🟢 |
| 3-5 | Moderado | Bajo | 🟡 |
| 6-7 | Alto | Moderado | 🟠 |
| 8-10 | Muy Alto | Alto | 🔴 |
| 11+ | Extremo | Muy Alto | 🟣 |

## 🔍 Logs

```bash
# Ver logs en tiempo real
docker logs -f uv-alert-vitoria

# Últimas 100 líneas
docker logs --tail 100 uv-alert-vitoria
```

## 🏷️ Tags Disponibles

- `latest`: Última versión estable
- `1.0.0`: Primera versión

## 📝 Notas

- El sistema ajusta automáticamente los tiempos al 50% para personas con medicación fotosensibilizante
- Los datos se obtienen de Euskalmet en tiempo real
- Compatible con arquitecturas AMD64 y ARM (Raspberry Pi)

## 🐛 Problemas Comunes

**No recibo alertas:**
- Verifica que has iniciado conversación con el bot
- Comprueba token y chat ID
- Revisa los logs

**Error de conexión:**
- Asegúrate de tener conexión a Internet
- Verifica que Euskalmet esté disponible

## 📧 Soporte

Para problemas o sugerencias, abre un issue en GitHub.

---
⚠️ **Importante**: Este sistema es una herramienta de ayuda. Siempre consulta con tu médico sobre la exposición solar con medicación fotosensibilizante.