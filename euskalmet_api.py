import requests
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class EuskalmetAPI:
    """Clase para interactuar con la API de Euskalmet"""
    
    def __init__(self):
        self.base_url = "https://api.euskalmet.euskadi.eus/uvi/estaciones/uvi"
        # Coordenadas de Vitoria-Gasteiz
        self.vitoria_lat = 42.8466
        self.vitoria_lon = -2.6725
        
    def get_uv_stations(self):
        """Obtiene todas las estaciones UV disponibles"""
        try:
            url = f"{self.base_url}/disponibles"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo estaciones: {e}")
            return None
    
    def get_current_uv(self):
        """Obtiene el UV actual para Vitoria-Gasteiz"""
        try:
            # Intentar obtener datos de la estación de Vitoria
            url = f"{self.base_url}/horaria"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Buscar datos de Vitoria en la respuesta
            for estacion in data:
                if 'vitoria' in estacion.get('nombre', '').lower():
                    # Obtener el último valor UV disponible
                    valores = estacion.get('valores', [])
                    if valores:
                        ultimo_valor = valores[-1]
                        return float(ultimo_valor.get('valor', 0))
            
            # Si no encontramos Vitoria, buscar la estación más cercana
            return self._get_nearest_station_uv(data)
            
        except Exception as e:
            logger.error(f"Error obteniendo UV actual: {e}")
            return None    
    def _get_nearest_station_uv(self, data):
        """Obtiene UV de la estación más cercana a Vitoria"""
        import math
        
        nearest_distance = float('inf')
        nearest_uv = 0
        
        for estacion in data:
            # Calcular distancia si tiene coordenadas
            lat = estacion.get('latitud')
            lon = estacion.get('longitud')
            
            if lat and lon:
                distance = math.sqrt(
                    (lat - self.vitoria_lat)**2 + 
                    (lon - self.vitoria_lon)**2
                )
                
                if distance < nearest_distance:
                    valores = estacion.get('valores', [])
                    if valores:
                        nearest_distance = distance
                        nearest_uv = float(valores[-1].get('valor', 0))
        
        return nearest_uv
    
    def get_forecast(self):
        """Obtiene el pronóstico UV para los próximos días"""
        try:
            url = f"{self.base_url}/prevision/localidad/048020"  # Código de Vitoria
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo pronóstico: {e}")
            return None