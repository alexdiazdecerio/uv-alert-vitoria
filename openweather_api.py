import requests
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class OpenWeatherMapAPI:
    """Cliente para la API de OpenWeatherMap UV Index"""
    
    def __init__(self):
        # API Key de OpenWeatherMap
        self.api_key = os.getenv('OPENWEATHER_API_KEY', '')
        
        # Base URL para UV Index
        self.base_url = "https://api.openweathermap.org/data/2.5/uvi"
        
        # Coordenadas de Vitoria-Gasteiz
        self.vitoria_lat = 42.8466
        self.vitoria_lon = -2.6725
        
        if not self.api_key:
            logger.warning("No se encontró OPENWEATHER_API_KEY, usando estimación por tiempo")
    
    def get_current_uv(self):
        """Obtiene el índice UV actual para Vitoria-Gasteiz"""
        if not self.api_key:
            logger.warning("API Key no configurada, usando estimación")
            return self._estimate_uv_by_time()
            
        try:
            params = {
                'lat': self.vitoria_lat,
                'lon': self.vitoria_lon,
                'appid': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # La API devuelve el UV index directamente en el campo 'value'
            if 'value' in data:
                uv_value = data['value']
                logger.info(f"UV obtenido de OpenWeatherMap: {uv_value}")
                return float(uv_value)
            else:
                logger.warning("Respuesta de OpenWeatherMap sin campo 'value'")
                return self._estimate_uv_by_time()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error conectando con OpenWeatherMap: {e}")
            return self._estimate_uv_by_time()
        except Exception as e:
            logger.error(f"Error procesando respuesta de OpenWeatherMap: {e}")
            return self._estimate_uv_by_time()
    
    def _estimate_uv_by_time(self):
        """Estima el UV basándose en la hora del día y época del año"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        month = now.month
        
        # No hay UV antes de las 8 o después de las 20
        if hour < 8 or hour > 20:
            return 0.0
            
        # Factor estacional
        if month in [6, 7, 8]:  # Verano
            seasonal_factor = 1.2
        elif month in [12, 1, 2]:  # Invierno
            seasonal_factor = 0.5
        elif month in [3, 4, 5]:  # Primavera
            seasonal_factor = 0.8
        else:  # Otoño
            seasonal_factor = 0.7
            
        # Factor horario
        decimal_hour = hour + minute/60
        if 12 <= decimal_hour <= 14:
            hour_factor = 1.0
        else:
            distance_from_noon = min(abs(decimal_hour - 13), 7)
            hour_factor = max(0.1, 1 - (distance_from_noon / 7))
        
        # UV estimado
        base_uv = 8.0
        estimated_uv = base_uv * seasonal_factor * hour_factor
        
        logger.info(f"UV estimado por tiempo: {round(estimated_uv, 1)}")
        return round(estimated_uv, 1)