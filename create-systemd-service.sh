#!/bin/bash

# Script para crear servicio systemd en Raspberry Pi

SERVICE_NAME="uv-alert-vitoria"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "Creando servicio systemd para UV Alert Vitoria..."

# Crear archivo de servicio
sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=UV Alert Vitoria-Gasteiz Monitor
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
Restart=always
RestartSec=10
User=$USER
WorkingDirectory=$HOME/uv-alert-vitoria
ExecStartPre=/usr/bin/docker-compose pull
ExecStart=/usr/bin/docker-compose up
ExecStop=/usr/bin/docker-compose down

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicio
sudo systemctl enable $SERVICE_NAME

echo "✅ Servicio creado y habilitado"
echo ""
echo "Comandos útiles:"
echo "  Iniciar:   sudo systemctl start $SERVICE_NAME"
echo "  Detener:   sudo systemctl stop $SERVICE_NAME"
echo "  Estado:    sudo systemctl status $SERVICE_NAME"
echo "  Logs:      sudo journalctl -u $SERVICE_NAME -f"