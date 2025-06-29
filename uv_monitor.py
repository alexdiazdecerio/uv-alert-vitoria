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
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError
import pytz
import json
from pathlib import Path
from openweather_api import CurrentUVIndexAPI

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
        
        # API de CurrentUVIndex (tiempo real)
        self.uv_api = CurrentUVIndexAPI()
        
        # Estado actual
        self.current_uv_index = 0
        self.is_dangerous = False
        self.last_alert_sent = None
        
        # Bot de Telegram
        self.bot = Bot(token=self.telegram_token)
        self.application = None
        
        # Timezone
        self.tz = pytz.timezone('Europe/Madrid')
        
        # Sistema de tracking de protector solar
        self.sunscreen_file = '/app/logs/sunscreen_tracking.json'
        self.sunscreen_data = self.load_sunscreen_data()
        
        # Horas de luz UV en Vitoria-Gasteiz (basado en solsticio de verano)
        # 21 junio: amanecer 06:34, anochecer 21:53
        # UV puede empezar ~1h después del amanecer y terminar ~1h antes del anochecer
        self.uv_start_hour = 7  # 07:30 aproximadamente
        self.uv_end_hour = 21   # 21:00 aproximadamente
    
    def is_uv_hours(self) -> bool:
        """Verifica si estamos en horas donde puede haber UV significativo"""
        now = datetime.now(self.tz)
        current_hour = now.hour
        return self.uv_start_hour <= current_hour <= self.uv_end_hour
    
    def should_check_uv(self) -> bool:
        """Determina si debemos hacer chequeo UV ahora"""
        if not self.is_uv_hours():
            return False
            
        # Durante horas UV, verificar cada 30 minutos
        return True
    
    def reset_daily_sunscreen_data(self):
        """Resetea datos de protector solar al cambiar el día"""
        if not self.sunscreen_data:
            return
            
        try:
            now = datetime.now(self.tz)
            applied_time_str = self.sunscreen_data.get('applied_at')
            
            if applied_time_str:
                applied_time = datetime.fromisoformat(applied_time_str)
                # Si la aplicación fue en un día diferente, resetear
                if applied_time.date() != now.date():
                    logger.info("Reseteando datos de protector solar - nuevo día")
                    self.sunscreen_data = {}
                    self.save_sunscreen_data()
                    
        except Exception as e:
            logger.error(f"Error reseteando datos de protector solar: {e}")    
    def get_uv_data(self) -> Optional[float]:
        """Obtiene índice UV actual de CurrentUVIndex en tiempo real"""
        try:
            uv_index = self.uv_api.get_current_uv()
            
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
    
    def calculate_burn_times(self, uv_index: float) -> tuple:
        """Calcula tiempos de quemadura para piel normal y con medicación fotosensibilizante"""
        if uv_index <= 0:
            return (999, 999)  # Sin UV, no hay riesgo de quemadura
            
        # Tiempo base para piel tipo II (piel clara normal) - referencia estándar
        normal_skin_base = 100  # minutos
        
        # Tiempo para piel normal (sin medicación)
        normal_burn_time = int(normal_skin_base / uv_index)
        
        # Tiempo con medicación fotosensibilizante (50% del tiempo normal)
        photosensitive_burn_time = int(normal_burn_time * 0.5)
        
        return (max(normal_burn_time, 5), max(photosensitive_burn_time, 3))    
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
            
            # Verificar recordatorios de protector solar
            if self.check_sunscreen_expiry():
                await self.send_sunscreen_reminder()
            
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
            normal_burn, photosensitive_burn = self.calculate_burn_times(self.current_uv_index)
            
            message = f"""⚠️ <b>ALERTA UV - Vitoria-Gasteiz</b> ⚠️

{emoji} Índice UV: <b>{self.current_uv_index}</b> ({level_desc})

🌡️ El nivel de radiación UV ha superado el umbral seguro ({self.uv_threshold})

⏱️ <b>Tiempo máximo de exposición sin protección: {safe_time} minutos</b>

🔥 <b>Tiempo hasta quemadura:</b>
• Piel normal: {normal_burn} minutos
• Con medicación fotosensibilizante: {photosensitive_burn} minutos

⚠️ <b>ATENCIÓN:</b> Tu tiempo de protección ya está reducido al 50% por medicación.

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
    
    def load_sunscreen_data(self) -> dict:
        """Carga datos de aplicación de protector solar"""
        try:
            if Path(self.sunscreen_file).exists():
                with open(self.sunscreen_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error cargando datos de protector solar: {e}")
            return {}
    
    def save_sunscreen_data(self):
        """Guarda datos de aplicación de protector solar"""
        try:
            Path(self.sunscreen_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.sunscreen_file, 'w') as f:
                json.dump(self.sunscreen_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error guardando datos de protector solar: {e}")
    
    def calculate_sunscreen_protection_time(self, spf: int, uv_index: float) -> int:
        """Calcula duración de protección del protector solar en minutos"""
        # Tiempo base de protección natural según tipo de piel (en minutos)
        base_times = {
            1: 67,   # Tipo I - Muy clara
            2: 100,  # Tipo II - Clara  
            3: 200,  # Tipo III - Media
            4: 300,  # Tipo IV - Morena
            5: 400,  # Tipo V - Muy morena
            6: 500   # Tipo VI - Negra
        }
        
        base_protection = base_times.get(self.skin_type, 100)
        
        # Ajuste por medicación fotosensibilizante (50% menos tiempo)
        base_protection *= 0.5
        
        # Calcular tiempo de protección: base_time * SPF / UV_index
        if uv_index > 0:
            protection_time = int((base_protection * spf) / uv_index)
            # Límites prácticos: mínimo 30 min, máximo 4 horas
            return min(max(protection_time, 30), 240)
        
        return 120  # 2 horas por defecto si UV es 0
    
    async def handle_sunscreen_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja comando /crema para reportar aplicación de protector"""
        try:
            # Parsear SPF del comando (por defecto SPF 50)
            spf = 50
            if context.args:
                try:
                    spf = int(context.args[0])
                    if spf < 15 or spf > 100:
                        spf = 50
                except ValueError:
                    spf = 50
            
            now = datetime.now(self.tz)
            current_uv = self.current_uv_index or 0
            
            # Calcular tiempo de protección
            protection_time = self.calculate_sunscreen_protection_time(spf, current_uv)
            expiry_time = now + timedelta(minutes=protection_time)
            
            # Guardar datos
            self.sunscreen_data = {
                'applied_at': now.isoformat(),
                'spf': spf,
                'uv_at_application': current_uv,
                'expires_at': expiry_time.isoformat(),
                'protection_minutes': protection_time
            }
            self.save_sunscreen_data()
            
            # Respuesta al usuario
            level_desc, emoji = self.get_uv_level_description(current_uv)
            normal_burn, photosensitive_burn = self.calculate_burn_times(current_uv)
            
            burn_info = ""
            if current_uv > 0:
                burn_info = f"""

🔥 <b>Sin protección, quemadura en:</b>
• Piel normal: {normal_burn} min
• Con medicación fotosensibilizante: {photosensitive_burn} min"""
            
            message = f"""🧴 <b>Protector Solar Aplicado</b> ✅

☀️ <b>SPF {spf}</b> registrado correctamente

📊 <b>Condiciones actuales:</b>
• UV Index: {current_uv} ({level_desc} {emoji})
• Tipo de piel: {self.skin_type}{burn_info}

⏰ <b>Protección válida hasta:</b>
{expiry_time.strftime('%H:%M')} ({protection_time} minutos)

🔔 Te recordaré cuando necesites reaplicar la crema.

💡 <b>Consejo:</b> Reaplicar cada 2 horas o después de sudar/mojarse."""
            
            await update.message.reply_text(message, parse_mode='HTML')
            logger.info(f"Protector solar SPF {spf} aplicado a las {now.strftime('%H:%M')}")
            
        except Exception as e:
            logger.error(f"Error en comando /crema: {e}")
            await update.message.reply_text("❌ Error procesando comando. Intenta de nuevo.")
    
    async def handle_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja comando /status para ver estado de protección"""
        try:
            now = datetime.now(self.tz)
            level_desc, emoji = self.get_uv_level_description(self.current_uv_index)
            
            # Información de horas UV
            uv_hours_info = ""
            if self.is_uv_hours():
                uv_hours_info = f"☀️ <b>Horas UV activas</b> ({self.uv_start_hour}h-{self.uv_end_hour}h)"
            else:
                uv_hours_info = f"🌙 <b>Fuera de horas UV</b> ({self.uv_start_hour}h-{self.uv_end_hour}h)"
            
            # Calcular tiempos de quemadura
            normal_burn, photosensitive_burn = self.calculate_burn_times(self.current_uv_index)
            
            burn_info = ""
            if self.current_uv_index > 0:
                burn_info = f"""
🔥 <b>Tiempo hasta quemadura:</b>
• Piel normal: {normal_burn} min
• Con medicación fotosensibilizante: {photosensitive_burn} min"""
            
            message = f"""📊 <b>Estado UV - Vitoria-Gasteiz</b>

🌞 <b>UV Actual:</b> {self.current_uv_index} ({level_desc} {emoji})
🕐 <b>Hora:</b> {now.strftime('%H:%M')}
{uv_hours_info}{burn_info}

"""
            
            if self.sunscreen_data:
                applied_time = datetime.fromisoformat(self.sunscreen_data['applied_at'])
                expiry_time = datetime.fromisoformat(self.sunscreen_data['expires_at'])
                
                if now < expiry_time:
                    time_left = expiry_time - now
                    hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                    minutes, _ = divmod(remainder, 60)
                    
                    message += f"""🧴 <b>Protector Activo:</b>
• SPF: {self.sunscreen_data['spf']}
• Aplicado: {applied_time.strftime('%H:%M')}
• Tiempo restante: {hours}h {minutes}m
• Expira: {expiry_time.strftime('%H:%M')}

✅ <b>Estás protegido</b>"""
                else:
                    time_expired = now - expiry_time
                    hours_expired = int(time_expired.total_seconds() / 3600)
                    
                    message += f"""⚠️ <b>Protección Expirada</b>
• Expiró hace: {hours_expired}h
• Última aplicación: {applied_time.strftime('%H:%M')}

🧴 <b>¡Necesitas reaplicar protector solar!</b>"""
            else:
                message += f"""❌ <b>Sin protección registrada</b>

🧴 Usa /crema para reportar aplicación de protector solar"""
            
            await update.message.reply_text(message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error en comando /status: {e}")
            await update.message.reply_text("❌ Error obteniendo estado.")
    
    def check_sunscreen_expiry(self) -> bool:
        """Verifica si necesita recordatorio de reaplicación"""
        if not self.sunscreen_data:
            return False
            
        try:
            now = datetime.now(self.tz)
            expiry_time = datetime.fromisoformat(self.sunscreen_data['expires_at'])
            
            # Recordatorio 15 minutos antes de expirar
            reminder_time = expiry_time - timedelta(minutes=15)
            
            # Si estamos en ventana de recordatorio y no se ha enviado
            if (reminder_time <= now <= expiry_time and 
                not self.sunscreen_data.get('reminder_sent', False)):
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error verificando expiración de protector: {e}")
            return False
    
    async def send_sunscreen_reminder(self):
        """Envía recordatorio de reaplicación de protector solar"""
        try:
            now = datetime.now(self.tz)
            expiry_time = datetime.fromisoformat(self.sunscreen_data['expires_at'])
            spf = self.sunscreen_data['spf']
            level_desc, emoji = self.get_uv_level_description(self.current_uv_index)
            
            message = f"""⏰ <b>Recordatorio de Protector Solar</b> 🧴

⚠️ Tu protección SPF {spf} expira en 15 minutos

🌞 <b>UV Actual:</b> {self.current_uv_index} ({level_desc} {emoji})
🕐 <b>Expira a las:</b> {expiry_time.strftime('%H:%M')}

🧴 <b>Recomendación:</b>
• Reaplicar protector solar SPF 50+
• Asegurar cobertura uniforme
• No olvidar orejas, cuello y manos

💡 Usa /crema después de reaplicar para reiniciar el timer."""
            
            await self.send_telegram_message(message)
            
            # Marcar recordatorio como enviado
            self.sunscreen_data['reminder_sent'] = True
            self.save_sunscreen_data()
            
            logger.info("Recordatorio de protector solar enviado")
            
        except Exception as e:
            logger.error(f"Error enviando recordatorio de protector: {e}")    
    async def setup_telegram_bot(self):
        """Configura el bot de Telegram con comandos"""
        try:
            self.application = Application.builder().token(self.telegram_token).build()
            
            # Registrar comandos
            self.application.add_handler(CommandHandler("crema", self.handle_sunscreen_command))
            self.application.add_handler(CommandHandler("protector", self.handle_sunscreen_command))
            self.application.add_handler(CommandHandler("status", self.handle_status_command))
            
            logger.info("Bot de Telegram configurado con comandos: /crema, /protector, /status")
            
        except Exception as e:
            logger.error(f"Error configurando bot de Telegram: {e}")
    
    async def start_bot_polling(self):
        """Inicia el polling del bot de Telegram"""
        try:
            if self.application:
                await self.application.initialize()
                await self.application.start()
                await self.application.updater.start_polling(drop_pending_updates=True)
                logger.info("Bot polling iniciado correctamente")
        except Exception as e:
            logger.error(f"Error iniciando bot polling: {e}")
    
    async def stop_bot_polling(self):
        """Detiene el polling del bot de Telegram"""
        try:
            if self.application and self.application.updater.running:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
        except Exception as e:
            logger.error(f"Error deteniendo bot polling: {e}")
    
    async def uv_check_worker(self):
        """Worker para verificaciones UV periódicas (solo durante horas de luz UV)"""
        while True:
            try:
                # Resetear datos de protector solar al cambio de día
                self.reset_daily_sunscreen_data()
                
                # Solo verificar UV durante horas de luz
                if self.should_check_uv():
                    await self.check_uv_and_alert()
                    logger.info(f"Chequeo UV completado - Próximo en {self.check_interval} minutos")
                    await asyncio.sleep(self.check_interval * 60)
                else:
                    # Fuera de horas UV, verificar cada hora si hemos entrado en horas UV
                    now = datetime.now(self.tz)
                    logger.info(f"Fuera de horas UV ({now.hour}h) - Próximo chequeo en 1 hora")
                    await asyncio.sleep(3600)  # 1 hora
                    
            except Exception as e:
                logger.error(f"Error en verificación UV: {e}")
                await asyncio.sleep(60)  # Esperar 1 minuto antes de reintentar
    
    async def run_async(self):
        """Ejecuta el monitor de forma asíncrona"""
        try:
            # Configurar bot de Telegram
            await self.setup_telegram_bot()
            
            # Iniciar bot polling
            await self.start_bot_polling()
            
            # Primera verificación
            await self.check_uv_and_alert()
            
            # Ejecutar worker de verificación UV
            await self.uv_check_worker()
            
        except KeyboardInterrupt:
            logger.info("Deteniendo UV Monitor...")
        except Exception as e:
            logger.error(f"Error en run_async: {e}")
        finally:
            # Limpiar recursos
            await self.stop_bot_polling()
    
    def run(self):
        """Ejecuta el monitor"""
        logger.info("Iniciando UV Monitor para Vitoria-Gasteiz")
        logger.info(f"Umbral UV: {self.uv_threshold}")
        logger.info(f"Tipo de piel: {self.skin_type}")
        logger.info(f"Intervalo de chequeo: {self.check_interval} minutos")
        logger.info(f"Horas de monitoreo UV: {self.uv_start_hour}:00 - {self.uv_end_hour}:00")
        
        # Verificar si estamos en horas UV al iniciar
        if self.is_uv_hours():
            logger.info("✅ Sistema iniciado durante horas UV - Monitoreo activo")
        else:
            logger.info("🌙 Sistema iniciado fuera de horas UV - Esperando horas de luz")
        
        # Ejecutar de forma asíncrona
        asyncio.run(self.run_async())


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