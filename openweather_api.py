import requests
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class CurrentUVIndexAPI:
    """Cliente para la API de CurrentUVIndex.com con respaldo OpenUV - datos UV en tiempo real"""
    
    def __init__(self):
        # Base URL para CurrentUVIndex (sin API key necesaria)
        self.base_url = "https://currentuvindex.com/api/v1/uvi"
        
        # OpenUV API como respaldo (requiere API key gratuita)
        self.openuv_base_url = "https://api.openuv.io/api/v1/uv"
        self.openuv_api_key = os.getenv('OPENUV_API_KEY')
        
        # Coordenadas de Vitoria-Gasteiz
        self.vitoria_lat = 42.8466
        self.vitoria_lon = -2.6725
        
        logger.info("Usando CurrentUVIndex API (principal) y OpenUV API (respaldo) para datos UV")
    
    def get_current_uv(self):
        """Obtiene el índice UV actual para Vitoria-Gasteiz en tiempo real"""
        # Intentar primero CurrentUVIndex
        uv_value = self._try_currentuvindex()
        if uv_value is not None:
            return uv_value
            
        # Si falla, intentar OpenUV
        uv_value = self._try_openuv()
        if uv_value is not None:
            return uv_value
            
        # Si ambas fallan, usar estimación
        logger.warning("Todas las APIs UV fallaron, usando estimación por tiempo")
        return self._estimate_uv_by_time()
    
    def _try_currentuvindex(self):
        """Intenta obtener datos UV de CurrentUVIndex.com"""
        try:
            params = {
                'latitude': self.vitoria_lat,
                'longitude': self.vitoria_lon
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar respuesta exitosa
            if not data.get('ok', False):
                logger.warning("CurrentUVIndex API respuesta no válida")
                return None
            
            # Obtener UV actual del campo 'now'
            now_data = data.get('now', {})
            if 'uvi' not in now_data:
                logger.warning("CurrentUVIndex API sin campo 'uvi'")
                return None
                
            uv_value = now_data['uvi']
            api_time = now_data.get('time', '')
            
            # Verificar si los datos están desactualizados (más de 75 minutos)
            if self._is_data_stale(api_time):
                logger.warning(f"CurrentUVIndex datos desactualizados: {api_time}")
                return None
                
            logger.info(f"UV obtenido de CurrentUVIndex: {uv_value} (fecha: {api_time})")
            return float(uv_value)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error conectando con CurrentUVIndex API: {e}")
            return None
        except Exception as e:
            logger.error(f"Error procesando respuesta de CurrentUVIndex: {e}")
            return None
    
    def _try_openuv(self):
        """Intenta obtener datos UV de OpenUV API"""
        if not self.openuv_api_key:
            logger.warning("OpenUV API key no configurada")
            return None
            
        try:
            headers = {'x-access-token': self.openuv_api_key}
            params = {
                'lat': self.vitoria_lat,
                'lng': self.vitoria_lon
            }
            
            response = requests.get(self.openuv_base_url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar respuesta exitosa
            if data.get('error'):
                logger.error(f"OpenUV API error: {data.get('error')}")
                return None
                
            result = data.get('result', {})
            if 'uv' not in result:
                logger.warning("OpenUV API sin campo 'uv'")
                return None
                
            uv_value = result['uv']
            api_time = result.get('uv_time', '')
            
            logger.info(f"UV obtenido de OpenUV: {uv_value} (fecha: {api_time})")
            return float(uv_value)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error conectando con OpenUV API: {e}")
            return None
        except Exception as e:
            logger.error(f"Error procesando respuesta de OpenUV: {e}")
            return None
    
    def _is_data_stale(self, api_time_str):
        """Verifica si los datos están desactualizados (más de 75 minutos)"""
        try:
            from datetime import datetime, timezone, timedelta
            
            # Parsear tiempo de la API
            api_time = datetime.fromisoformat(api_time_str.replace('Z', '+00:00'))
            current_time = datetime.now(timezone.utc)
            
            # Verificar si han pasado más de 75 minutos
            # Las APIs UV deberían actualizarse cada hora máximo
            time_diff = current_time - api_time
            return time_diff > timedelta(minutes=75)
            
        except Exception as e:
            logger.warning(f"Error verificando tiempo de datos: {e}")
            return False
    
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