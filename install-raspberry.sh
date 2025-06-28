#!/bin/bash

# Script de instalación para Raspberry Pi
# UV Alert Vitoria-Gasteiz

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}UV Alert Vitoria - Instalador${NC}"
echo -e "${BLUE}================================${NC}\n"

# Función para solicitar datos
get_input() {
    local prompt=$1
    local var_name=$2
    local default=$3
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " value
        value=${value:-$default}
    else
        read -p "$prompt: " value
        while [ -z "$value" ]; do
            echo -e "${RED}Este campo es obligatorio${NC}"
            read -p "$prompt: " value
        done
    fi
    
    eval "$var_name='$value'"
}
# Verificar que estamos en Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo -e "${YELLOW}Advertencia: No se detectó una Raspberry Pi${NC}"
    read -p "¿Deseas continuar de todos modos? (s/n): " continue
    if [ "$continue" != "s" ]; then
        exit 0
    fi
fi

# Verificar Docker
echo -e "${YELLOW}Verificando Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker no está instalado${NC}"
    echo -e "${YELLOW}Instalando Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✓ Docker instalado${NC}"
    echo -e "${YELLOW}Por favor, cierra sesión y vuelve a entrar para aplicar los cambios${NC}"
    exit 0
fi

# Verificar docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Instalando docker-compose...${NC}"
    sudo apt-get update
    sudo apt-get install -y docker-compose
fi

echo -e "${GREEN}✓ Docker y docker-compose están instalados${NC}\n"
# Crear directorio de instalación
INSTALL_DIR="$HOME/uv-alert-vitoria"
echo -e "${YELLOW}Creando directorio de instalación en $INSTALL_DIR${NC}"
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Descargar archivos necesarios
echo -e "${YELLOW}Descargando archivos de configuración...${NC}"

# Crear docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  uv-monitor:
    image: ${DOCKER_USERNAME}/uv-alert-vitoria:latest
    container_name: uv-alert-vitoria
    restart: unless-stopped
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
      - UV_THRESHOLD=${UV_THRESHOLD:-6}
      - SKIN_TYPE=${SKIN_TYPE:-2}
      - CHECK_INTERVAL_MINUTES=${CHECK_INTERVAL_MINUTES:-30}
      - TZ=Europe/Madrid
    volumes:
      - ./logs:/app/logs
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF

echo -e "${GREEN}✓ docker-compose.yml creado${NC}"
# Solicitar configuración
echo -e "\n${BLUE}Configuración del Sistema${NC}"
echo -e "${BLUE}=========================${NC}\n"

echo -e "${YELLOW}Necesitarás:${NC}"
echo "1. Token del bot de Telegram (obtener de @BotFather)"
echo "2. Tu ID de chat de Telegram (obtener de @userinfobot)"
echo "3. Tu usuario de Docker Hub"
echo ""

get_input "Token del bot de Telegram" TELEGRAM_BOT_TOKEN
get_input "ID de chat de Telegram" TELEGRAM_CHAT_ID
get_input "Usuario de Docker Hub" DOCKER_USERNAME

echo -e "\n${YELLOW}Configuración de alertas:${NC}"
get_input "Umbral de UV peligroso (6-11)" UV_THRESHOLD "6"

echo -e "\n${YELLOW}Tipo de piel:${NC}"
echo "1. Muy clara (se quema siempre)"
echo "2. Clara (se quema fácilmente)"
echo "3. Media (se quema moderadamente)"
echo "4. Morena (se quema mínimamente)"
echo "5. Muy morena (raramente se quema)"
echo "6. Negra (nunca se quema)"
get_input "Tu tipo de piel (1-6)" SKIN_TYPE "2"

get_input "Intervalo de verificación (minutos)" CHECK_INTERVAL_MINUTES "30"
# Crear archivo .env
echo -e "\n${YELLOW}Creando archivo de configuración...${NC}"
cat > .env << EOF
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID
UV_THRESHOLD=$UV_THRESHOLD
SKIN_TYPE=$SKIN_TYPE
CHECK_INTERVAL_MINUTES=$CHECK_INTERVAL_MINUTES
DOCKER_USERNAME=$DOCKER_USERNAME
EOF

echo -e "${GREEN}✓ Configuración guardada${NC}"

# Crear directorio de logs
mkdir -p logs

# Iniciar el servicio
echo -e "\n${YELLOW}Iniciando el servicio...${NC}"
docker-compose pull
docker-compose up -d

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ ¡Instalación completada con éxito!${NC}"
    echo -e "\n${BLUE}El sistema está monitoreando el UV en Vitoria-Gasteiz${NC}"
    echo -e "${BLUE}Recibirás alertas en Telegram cuando el UV supere $UV_THRESHOLD${NC}"
    
    echo -e "\n${YELLOW}Comandos útiles:${NC}"
    echo "Ver logs:        docker-compose logs -f"
    echo "Detener:         docker-compose down"
    echo "Reiniciar:       docker-compose restart"
    echo "Ver estado:      docker ps"
    
    echo -e "\n${GREEN}Los logs se guardan en: $INSTALL_DIR/logs/${NC}"
else
    echo -e "\n${RED}Error al iniciar el servicio${NC}"
    echo "Verifica los logs con: docker-compose logs"
fi