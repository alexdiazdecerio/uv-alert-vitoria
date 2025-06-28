# UV Alert Vitoria-Gasteiz 🌞

[![Docker Hub](https://img.shields.io/badge/docker-alexdiazdecerio%2Fuv--alert--vitoria-blue)](https://hub.docker.com/r/alexdiazdecerio/uv-alert-vitoria)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Sistema inteligente de monitoreo de radiación UV para Vitoria-Gasteiz con alertas por Telegram y tracking de protector solar.

## 🎯 ¿Qué hace?

Este sistema monitorea continuamente el índice de radiación ultravioleta (UV) en Vitoria-Gasteiz usando datos en tiempo real y te envía alertas a Telegram cuando:

- ☀️ **Alertas UV**: El UV supera el umbral peligroso que configures
- ✅ **Nivel seguro**: El UV vuelve a niveles seguros
- 🧴 **Tracking de protector**: Recordatorios inteligentes para reaplicar crema solar
- ⏰ **Cálculos personalizados**: Tiempo de protección según tu tipo de piel y SPF

Especialmente diseñado para personas con **fotosensibilidad** o que toman **medicación fotosensibilizante**.

## 🚀 Instalación Rápida

### Opción 1: Docker (Recomendado)

```bash
docker run -d \
  --name uv-alert \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN="tu_token" \
  -e TELEGRAM_CHAT_ID="tu_chat_id" \
  -e UV_THRESHOLD=6 \
  -e SKIN_TYPE=2 \
  -v ./logs:/app/logs \
  alexdiazdecerio/uv-alert-vitoria:latest
```

### Opción 2: Docker Compose

1. **Clona el repositorio:**
```bash
git clone https://github.com/alexdiazdecerio/uv-alert-vitoria.git
cd uv-alert-vitoria
```

2. **Configura las variables:**
```bash
cp .env.example .env
nano .env  # Edita con tus datos
```

3. **Ejecuta:**
```bash
docker-compose up -d
```

## 🧴 Comandos de Telegram

### Tracking de Protector Solar
- **`/crema`** o **`/protector`** - Reporta aplicación de protector solar (SPF 50 por defecto)
- **`/crema 30`** - Reporta aplicación con SPF específico (ej: SPF 30)
- **`/status`** - Muestra estado actual de UV y protección solar

### Ejemplo de uso:
```
Usuario: /crema 50
Bot: 🧴 Protector Solar Aplicado ✅
     ☀️ SPF 50 registrado correctamente
     📊 UV Index: 8.2 (Muy Alto 🔴)
     ⏰ Protección válida hasta: 14:30 (120 minutos)
     🔔 Te recordaré cuando necesites reaplicar

Usuario: /status  
Bot: 📊 Estado UV - Vitoria-Gasteiz
     🌞 UV Actual: 8.2 (Muy Alto 🔴)
     🧴 Protector Activo: SPF 50
     ⏰ Tiempo restante: 1h 45m
```

## ✨ Características Principales

- 🌞 **Datos UV en tiempo real** - API CurrentUVIndex.com sin límites ni API keys
- 📱 **Alertas inteligentes** - Notificaciones cuando UV supera/baja del umbral
- 🧴 **Sistema de protector solar** - Tracking completo con recordatorios automáticos
- ⏱️ **Cálculos personalizados** - Tiempo de protección según piel, SPF y UV actual
- 💊 **Medicación fotosensibilizante** - Ajuste automático (50% reducción de tiempos)
- 🔔 **Recordatorios proactivos** - Aviso 15 minutos antes de que expire la protección
- 🐳 **Fácil despliegue** - Docker listo para Raspberry Pi y otros sistemas
- 📊 **Logs detallados** - Monitoreo completo del sistema

## 📋 Requisitos Previos

1. **Bot de Telegram**:
   - Habla con [@BotFather](https://t.me/botfather) en Telegram
   - Crea un nuevo bot con `/newbot`
   - Guarda el token que te proporciona

2. **Tu Chat ID de Telegram**:
   - Habla con [@userinfobot](https://t.me/userinfobot)
   - Te dirá tu ID de usuario

3. **Docker instalado** (si usas Docker)

## ⚙️ Configuración

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

**Nota**: El programa ajusta automáticamente los tiempos al 50% para medicación fotosensibilizante.

## 📊 Niveles de Índice UV

| Índice UV | Nivel | Emoji | Riesgo |
|-----------|-------|-------|---------|
| 0-2 | Bajo | 🟢 | Mínimo |
| 3-5 | Moderado | 🟡 | Bajo |
| 6-7 | Alto | 🟠 | Moderado |
| 8-10 | Muy Alto | 🔴 | Alto |
| 11+ | Extremo | 🟣 | Muy Alto |

## 📖 Documentación Adicional

- 🍓 [**Guía completa para Raspberry Pi**](RASPBERRY_INSTALL.md)
- 🐳 [Documentación de Docker Hub](https://hub.docker.com/r/alexdiazdecerio/uv-alert-vitoria)

## 🔍 Comandos Útiles

```bash
# Ver estado del contenedor
docker ps

# Ver logs en tiempo real
docker logs -f uv-alert-vitoria

# Detener el servicio
docker-compose down

# Reiniciar el servicio
docker-compose restart

# Actualizar a nueva versión
docker-compose pull && docker-compose up -d
```

## 🔧 Solución de Problemas

### Bot no responde a comandos
```bash
# Verificar logs del contenedor
docker logs uv-alert-vitoria

# Verificar que el bot esté activo
# Debería aparecer: "Bot polling iniciado correctamente"
```

### No recibo alertas UV
1. **Verifica configuración**: Token y Chat ID correctos en `.env`
2. **Prueba el bot**: Envía `/status` al bot para verificar conectividad
3. **Revisa logs**: `docker logs -f uv-alert-vitoria`

### Datos UV no actualizados
- Los datos se obtienen de CurrentUVIndex.com en tiempo real
- Verificar logs para errores de conexión de red

## 📝 Estructura del Proyecto

```
uv-alert-vitoria/
├── uv_monitor.py          # Monitor principal con tracking de protector
├── openweather_api.py     # Cliente API CurrentUVIndex (tiempo real) 
├── Dockerfile             # Imagen Docker
├── docker-compose.yml     # Configuración Docker Compose
├── requirements.txt       # Dependencias Python
├── .env.example          # Plantilla de configuración
├── RASPBERRY_INSTALL.md  # Guía Raspberry Pi
└── README.md             # Este archivo
```

## 🚀 Historial de Versiones

- **v4.0.2** - Corrección de event loop asyncio para bot polling
- **v4.0.1** - Implementación de polling asíncrono para comandos de Telegram
- **v4.0.0** - Sistema completo de tracking de protector solar con comandos
- **v3.x** - Migración a CurrentUVIndex.com para datos UV tiempo real
- **v2.x** - Integración OpenWeatherMap 
- **v1.x** - Versión inicial con Euskalmet API

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea tu rama de características (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📜 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## ⚠️ Aviso Legal

Este sistema es una herramienta de ayuda informativa. Siempre consulta con tu médico sobre la exposición solar, especialmente si tomas medicación fotosensibilizante.

## 👨‍💻 Autor

Alejandro Díaz de Cerio

---

Hecho con ❤️ para la comunidad de Vitoria-Gasteiz