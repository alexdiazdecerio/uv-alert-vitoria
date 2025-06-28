#!/usr/bin/env python3
"""
UV Alert System for Vitoria-Gasteiz
Monitors UV radiation levels and sends Telegram alerts
"""

import os
import requests
import json
import schedule
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
import asyncio
from telegram import Bot
from telegram.error import TelegramError
import pytz
from openweather_api import OpenWeatherMapAPI

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/uv_monitor.log')
    ]
)

logger = logging.getLogger(__name__)

class UVMonitor:
    """Monitor de radiación UV para Vitoria-Gasteiz"""
    
    def __init__(self):
        # Configuración desde variables de entorno
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.uv_threshold = float(os.getenv('UV_THRESHOLD', '6'))
        self.skin_type = int(os.getenv('SKIN_TYPE', '2'))
        self.check_interval = int(os.getenv('CHECK_INTERVAL_MINUTES', '30'))
        
        # API de OpenWeatherMap
        self.openweather = OpenWeatherMapAPI()
        
        # Estado actual
        self.current_uv_index = 0
        self.is_dangerous = False
        self.last_alert_sent = None
        
        # Bot de Telegram
        self.bot = Bot(token=self.telegram_token)
        
        # Timezone
        self.tz = pytz.timezone('Europe/Madrid')    
    def get_uv_data(self) -> Optional[float]:
        """Obtiene índice UV actual de OpenWeatherMap"""
        try:
            uv_index = self.openweather.get_current_uv()
            
            if uv_index is not None:
                logger.info(f"Índice UV obtenido: {uv_index}")
                return uv_index
            else:
                logger.warning("No se pudo obtener el índice UV")
                return None
            
        except Exception as e:
            logger.error(f"Error obteniendo datos UV: {e}")
            return None    
    def calculate_safe_exposure_time(self, uv_index: float) -> int:
        """Calcula el tiempo seguro de exposición según el tipo de piel"""
        # Tiempos base en minutos para quemadura según tipo de piel (sin protección)
        base_times = {
            1: 67,   # Tipo I - Muy clara
            2: 100,  # Tipo II - Clara
            3: 200,  # Tipo III - Media
            4: 300,  # Tipo IV - Morena
            5: 400,  # Tipo V - Muy morena
            6: 500   # Tipo VI - Negra
        }
        
        # Ajuste por medicación fotosensibilizante (reduce tiempo en 50%)
        base_time = base_times.get(self.skin_type, 100) * 0.5
        
        # Fórmula: tiempo_seguro = tiempo_base / UV_index
        if uv_index > 0:
            safe_time = int(base_time / uv_index)
            return max(safe_time, 5)  # Mínimo 5 minutos
        
        return 60  # Si UV es 0, tiempo seguro es alto    
    def get_uv_level_description(self, uv_index: float) -> Tuple[str, str]:
        """Obtiene descripción y emoji del nivel UV"""
        if uv_index < 3:
            return "Bajo", "🟢"
        elif uv_index < 6:
            return "Moderado", "🟡"
        elif uv_index < 8:
            return "Alto", "🟠"
        elif uv_index < 11:
            return "Muy Alto", "🔴"
        else:
            return "Extremo", "🟣"
    
    async def send_telegram_message(self, message: str):
        """Envía mensaje a Telegram"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info(f"Mensaje enviado: {message[:50]}...")
        except TelegramError as e:
            logger.error(f"Error enviando mensaje Telegram: {e}")    
    async def check_uv_and_alert(self):
        """Verifica UV y envía alertas si es necesario"""
        uv_index = self.get_uv_data()
        
        if uv_index is None:
            logger.warning("No se pudieron obtener datos UV")
            return
        
        try:
            self.current_uv_index = float(uv_index)
            
            # Determinar si es peligroso
            is_dangerous_now = self.current_uv_index >= self.uv_threshold
            
            # Generar mensaje si hay cambio de estado
            if is_dangerous_now != self.is_dangerous:
                await self.send_alert(is_dangerous_now)
                self.is_dangerous = is_dangerous_now
            # También enviar alerta si UV baja por debajo del umbral
            elif self.is_dangerous and self.current_uv_index < self.uv_threshold:
                await self.send_safe_alert()
                self.is_dangerous = False
            
            # Log del estado actual
            level_desc, emoji = self.get_uv_level_description(self.current_uv_index)
            logger.info(f"UV actual: {self.current_uv_index} - {level_desc} {emoji}")
            
        except Exception as e:
            logger.error(f"Error procesando datos UV: {e}")    
    async def send_alert(self, is_dangerous: bool):
        """Envía alerta según el estado"""
        now = datetime.now(self.tz)
        level_desc, emoji = self.get_uv_level_description(self.current_uv_index)
        
        if is_dangerous:
            safe_time = self.calculate_safe_exposure_time(self.current_uv_index)
            
            message = f"""⚠️ <b>ALERTA UV - Vitoria-Gasteiz</b> ⚠️

{emoji} Índice UV: <b>{self.current_uv_index}</b> ({level_desc})

🌡️ El nivel de radiación UV ha superado el umbral seguro ({self.uv_threshold})

⏱️ <b>Tiempo máximo de exposición sin protección: {safe_time} minutos</b>

⚠️ <b>ATENCIÓN:</b> Debido a tu medicación fotosensibilizante, este tiempo ya está reducido al 50%.

🧴 <b>Recomendaciones:</b>
• Evita la exposición solar directa
• Usa protector solar SPF 50+
• Cubre tu piel con ropa
• Usa sombrero y gafas de sol
• Busca la sombra

🕐 Hora: {now.strftime('%H:%M')}
📅 Fecha: {now.strftime('%d/%m/%Y')}"""
        else:
            message = f"""✅ <b>UV SEGURO - Vitoria-Gasteiz</b> ✅

{emoji} Índice UV: <b>{self.current_uv_index}</b> ({level_desc})

🌤️ El nivel de radiación UV ha bajado a niveles seguros.

💡 Puedes salir con precauciones normales.

🕐 Hora: {now.strftime('%H:%M')}
📅 Fecha: {now.strftime('%d/%m/%Y')}"""
        
        await self.send_telegram_message(message)
    
    async def send_safe_alert(self):
        """Envía alerta cuando UV baja del umbral peligroso"""
        now = datetime.now(self.tz)
        level_desc, emoji = self.get_uv_level_description(self.current_uv_index)
        
        message = f"""✅ <b>UV SEGURO - Vitoria-Gasteiz</b> ✅

{emoji} Índice UV: <b>{self.current_uv_index}</b> ({level_desc})

🌤️ El nivel de radiación UV ha bajado por debajo del umbral peligroso ({self.uv_threshold}).

💡 Ahora puedes salir con las precauciones normales para tu tipo de piel.

🕐 Hora: {now.strftime('%H:%M')}
📅 Fecha: {now.strftime('%d/%m/%Y')}"""
        
        await self.send_telegram_message(message)    
    def run(self):
        """Ejecuta el monitor"""
        logger.info("Iniciando UV Monitor para Vitoria-Gasteiz")
        logger.info(f"Umbral UV: {self.uv_threshold}")
        logger.info(f"Tipo de piel: {self.skin_type}")
        logger.info(f"Intervalo de chequeo: {self.check_interval} minutos")
        
        # Primera verificación
        asyncio.run(self.check_uv_and_alert())
        
        # Programar verificaciones periódicas
        schedule.every(self.check_interval).minutes.do(
            lambda: asyncio.run(self.check_uv_and_alert())
        )
        
        # Mantener el programa ejecutándose
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto


def main():
    """Función principal"""
    # Verificar variables de entorno necesarias
    required_env = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
    missing = [var for var in required_env if not os.getenv(var)]
    
    if missing:
        logger.error(f"Faltan variables de entorno: {', '.join(missing)}")
        exit(1)
    
    # Crear directorio de logs si no existe
    os.makedirs('/app/logs', exist_ok=True)
    
    # Iniciar monitor
    monitor = UVMonitor()
    monitor.run()


if __name__ == "__main__":
    main()