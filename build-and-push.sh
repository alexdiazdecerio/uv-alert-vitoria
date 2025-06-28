#!/bin/bash

# Script para construir y subir imagen a Docker Hub

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}UV Alert Vitoria - Docker Build & Push${NC}"
echo "========================================"

# Verificar que existe el archivo .env
if [ ! -f .env ]; then
    echo -e "${RED}Error: No se encontró el archivo .env${NC}"
    echo "Por favor, copia .env.example a .env y configura tus variables"
    exit 1
fi

# Cargar variables de entorno
source .env

# Verificar que DOCKER_USERNAME está configurado
if [ -z "$DOCKER_USERNAME" ]; then
    echo -e "${RED}Error: DOCKER_USERNAME no está configurado en .env${NC}"
    exit 1
fi

echo -e "${GREEN}Usuario de Docker Hub: $DOCKER_USERNAME${NC}"

# Login en Docker Hub
echo -e "\n${YELLOW}Iniciando sesión en Docker Hub...${NC}"
docker login

# Construir imagen
echo -e "\n${YELLOW}Construyendo imagen Docker...${NC}"
docker build -t $DOCKER_USERNAME/uv-alert-vitoria:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Imagen construida exitosamente${NC}"
else
    echo -e "${RED}✗ Error al construir la imagen${NC}"
    exit 1
fi
# Subir imagen a Docker Hub
echo -e "\n${YELLOW}Subiendo imagen a Docker Hub...${NC}"
docker push $DOCKER_USERNAME/uv-alert-vitoria:latest

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Imagen subida exitosamente${NC}"
    echo -e "\n${GREEN}¡Listo! Puedes usar la imagen con:${NC}"
    echo -e "${YELLOW}docker pull $DOCKER_USERNAME/uv-alert-vitoria:latest${NC}"
    echo -e "\n${GREEN}O en tu Raspberry Pi, ejecuta:${NC}"
    echo -e "${YELLOW}docker-compose up -d${NC}"
else
    echo -e "${RED}✗ Error al subir la imagen${NC}"
    exit 1
fi

echo -e "\n${GREEN}✓ Proceso completado${NC}"