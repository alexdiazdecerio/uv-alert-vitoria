#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración de Telegram
"""

import os
import sys
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

async def test_telegram():
    """Prueba la conexión con Telegram"""
    
    # Obtener configuración
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("❌ Error: Falta TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en .env")
        return False
    
    print(f"📱 Probando conexión con Telegram...")
    print(f"   Chat ID: {chat_id}")
    
    try:
        # Crear bot
        bot = Bot(token=token)
        
        # Obtener información del bot
        bot_info = await bot.get_me()
        print(f"✅ Bot conectado: @{bot_info.username}")
        
        # Enviar mensaje de prueba
        message = """🧪 <b>Mensaje de prueba</b>

✅ La configuración de Telegram es correcta.
🌞 El sistema UV Alert está listo para funcionar.

Este es un mensaje de prueba del sistema de alertas UV para Vitoria-Gasteiz."""
        
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML'
        )
        
        print("✅ Mensaje de prueba enviado correctamente")
        print("\n🎉 ¡Todo listo! Puedes ejecutar el sistema.")
        return True
        
    except TelegramError as e:
        print(f"❌ Error de Telegram: {e}")
        print("\nPosibles causas:")
        print("- Token incorrecto")
        print("- Chat ID incorrecto") 
        print("- El bot no tiene permisos para enviar mensajes")
        print("\n⚠️  IMPORTANTE:")
        print(f"1. Busca a tu bot @{bot_info.username} en Telegram")
        print("2. Inicia una conversación con él (pulsa 'Start' o envía /start)")
        print("3. Vuelve a ejecutar este script")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    if not os.path.exists('.env'):
        print("❌ No se encontró el archivo .env")
        print("   Copia .env.example a .env y configura tus datos")
        sys.exit(1)
    
    # Ejecutar test
    success = asyncio.run(test_telegram())
    sys.exit(0 if success else 1)