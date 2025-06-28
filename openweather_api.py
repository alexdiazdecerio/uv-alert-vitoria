import requests
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class CurrentUVIndexAPI:
    """Cliente para la API de CurrentUVIndex.com - datos UV en tiempo real sin API key"""
    
    def __init__(self):
        # Base URL para CurrentUVIndex (sin API key necesaria)
        self.base_url = "https://currentuvindex.com/api/v1/uvi"
        
        # Coordenadas de Vitoria-Gasteiz
        self.vitoria_lat = 42.8466
        self.vitoria_lon = -2.6725
        
        logger.info("Usando CurrentUVIndex API para datos UV en tiempo real")
    
    def get_current_uv(self):
        """Obtiene el índice UV actual para Vitoria-Gasteiz en tiempo real"""
        try:
            # Obtener datos UV en tiempo real (sin API key)
            params = {
                'latitude': self.vitoria_lat,
                'longitude': self.vitoria_lon
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar respuesta exitosa
            if not data.get('ok', False):
                logger.warning("CurrentUVIndex API respuesta no válida, usando estimación")
                return self._estimate_uv_by_time()
            
            # Obtener UV actual del campo 'now'
            now_data = data.get('now', {})
            if 'uvi' in now_data:
                uv_value = now_data['uvi']
                api_time = now_data.get('time', '')
                
                logger.info(f"UV obtenido de CurrentUVIndex (tiempo real): {uv_value} (fecha: {api_time})")
                return float(uv_value)
            else:
                logger.warning("CurrentUVIndex API sin campo 'uvi', usando estimación")
                return self._estimate_uv_by_time()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error conectando con CurrentUVIndex API: {e}")
            return self._estimate_uv_by_time()
        except Exception as e:
            logger.error(f"Error procesando respuesta de CurrentUVIndex: {e}")
            return self._estimate_uv_by_time()
    
    def _estimate_uv_by_time(self):
        """Estima el UV basándose en la hora del día y época del año"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        month = now.month
        
        # Horarios de UV según estación (aproximados para Vitoria-Gasteiz)
        if month in [6, 7, 8]:  # Verano - días más largos
            uv_start_hour = 5
            uv_end_hour = 21
        elif month in [4, 5, 9, 10]:  # Primavera/Otoño  
            uv_start_hour = 6
            uv_end_hour = 19
        else:  # Invierno - días más cortos
            uv_start_hour = 7
            uv_end_hour = 17
            
        # No hay UV fuera de las horas solares
        if hour < uv_start_hour or hour > uv_end_hour:
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