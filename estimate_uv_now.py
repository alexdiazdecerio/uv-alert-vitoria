#!/usr/bin/env python3
"""
Script para estimar el índice UV actual en Vitoria-Gasteiz
"""

from datetime import datetime
import math

def estimate_current_uv():
    """Estima el UV actual basándose en hora y época del año"""
    
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    month = now.month
    
    print("🌞 ÍNDICE UV ESTIMADO - VITORIA-GASTEIZ")
    print("=" * 40)
    print(f"📅 Fecha: {now.strftime('%d/%m/%Y %H:%M')}")
    print("=" * 40)
    
    # No hay UV antes de las 8 o después de las 20
    if hour < 8 or hour > 20:
        uv_index = 0.0
        nivel = "Sin radiación UV 🌙"
    else:
        # Factor estacional
        if month in [6, 7, 8]:  # Verano
            seasonal_factor = 1.2
            estacion = "Verano ☀️"
        elif month in [12, 1, 2]:  # Invierno
            seasonal_factor = 0.5
            estacion = "Invierno ❄️"
        elif month in [3, 4, 5]:  # Primavera
            seasonal_factor = 0.8
            estacion = "Primavera 🌸"
        else:  # Otoño
            seasonal_factor = 0.7
            estacion = "Otoño 🍂"
            
        # Factor horario (máximo entre 12-14h)
        decimal_hour = hour + minute/60
        if 12 <= decimal_hour <= 14:
            hour_factor = 1.0
        else:
            # Decrece según nos alejamos del mediodía
            distance_from_noon = min(abs(decimal_hour - 13), 7)
            hour_factor = max(0.1, 1 - (distance_from_noon / 7))
        
        # UV estimado
        base_uv = 8.0  # UV máximo típico en verano en Vitoria
        uv_index = round(base_uv * seasonal_factor * hour_factor, 1)
        
        # Determinar nivel
        if uv_index < 3:
            nivel = "Bajo 🟢"
        elif uv_index < 6:
            nivel = "Moderado 🟡"
        elif uv_index < 8:
            nivel = "Alto 🟠"
        elif uv_index < 11:
            nivel = "Muy Alto 🔴"
        else:
            nivel = "Extremo 🟣"
    
    print(f"\n📊 Estimación UV: {uv_index}")
    print(f"🔢 Nivel: {nivel}")
    print(f"🗓️ Estación: {estacion}")
    
    if uv_index >= 6:
        print("\n⚠️  ¡PRECAUCIÓN! UV por encima del umbral seguro")
        print("   Usa protección solar y evita exposición prolongada")
    elif uv_index > 0:
        print("\n✅ UV en niveles seguros")
    
    print("\n💡 Nota: Esta es una estimación basada en:")
    print("   - Hora del día")
    print("   - Época del año")
    print("   - Latitud de Vitoria-Gasteiz")
    print("\n🔍 Para datos exactos, consulta:")
    print("   https://www.euskalmet.euskadi.eus")
    
    # Mostrar próximas horas
    if 8 <= hour < 18:
        print("\n📈 Estimación próximas horas:")
        for h in range(1, 4):
            future_hour = hour + h
            if future_hour <= 20:
                if 12 <= future_hour <= 14:
                    future_factor = 1.0
                else:
                    distance = min(abs(future_hour - 13), 7)
                    future_factor = max(0.1, 1 - (distance / 7))
                future_uv = round(base_uv * seasonal_factor * future_factor, 1)
                print(f"   {future_hour:02d}:00 → UV: {future_uv}")

if __name__ == "__main__":
    estimate_current_uv()