#!/usr/bin/env python3
"""
Script para consultar el índice UV actual en Vitoria-Gasteiz
"""

import requests
import json
from datetime import datetime

def get_current_uv():
    """Obtiene el UV actual de Euskalmet"""
    try:
        # URL de la API de Euskalmet
        url = "https://api.euskalmet.euskadi.eus/uvi/estaciones/uvi/horaria"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        print("🌞 ÍNDICE UV - EUSKALMET")
        print("=" * 40)
        print(f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print("=" * 40)
        
        # Buscar datos de Vitoria
        vitoria_found = False
        for estacion in data:
            nombre = estacion.get('nombre', '').lower()
            if 'vitoria' in nombre or 'gasteiz' in nombre:
                vitoria_found = True
                print(f"\n📍 Estación: {estacion.get('nombre', 'Desconocido')}")
                
                valores = estacion.get('valores', [])
                if valores:
                    # Obtener el último valor
                    ultimo = valores[-1]
                    uv_index = float(ultimo.get('valor', 0))
                    hora = ultimo.get('hora', 'N/A')
                    
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
                    
                    print(f"🔢 Índice UV: {uv_index}")
                    print(f"📊 Nivel: {nivel}")
                    print(f"🕐 Hora medición: {hora}")
                    
                    # Mostrar histórico del día
                    print(f"\n📈 Histórico del día ({len(valores)} mediciones):")
                    for i, val in enumerate(valores[-5:]):  # Últimas 5 mediciones
                        print(f"   {val.get('hora', 'N/A')} → UV: {val.get('valor', 0)}")
        
        if not vitoria_found:
            print("⚠️  No se encontraron datos específicos de Vitoria-Gasteiz")
            print("\n🏢 Estaciones disponibles:")
            for estacion in data[:5]:  # Mostrar primeras 5
                print(f"   - {estacion.get('nombre', 'Sin nombre')}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Tip: Visita https://www.euskalmet.euskadi.eus/radiacion-solar/")

if __name__ == "__main__":
    get_current_uv()