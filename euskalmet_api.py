import requests
from datetime import datetime, timedelta
import json
import logging
import os
import jwt
import time
import base64

logger = logging.getLogger(__name__)


class EuskalmetAPI:
    """Clase para interactuar con la API de Euskalmet usando JWT"""
    
    def __init__(self):
        # URLs de la API de Euskalmet
        self.base_url = "https://api.euskadi.eus/euskalmet"
        
        # Coordenadas de Vitoria-Gasteiz
        self.vitoria_lat = 42.8466
        self.vitoria_lon = -2.6725
        
        # Claves RSA desde variables de entorno o hardcoded temporalmente
        self.private_key = os.getenv('EUSKALMET_API_KEY_PRIVATE', '')
        self.public_key = os.getenv('EUSKALMET_API_KEY_PUBLIC', '')
        
        # Email asociado a la API key
        self.api_email = os.getenv('EUSKALMET_API_EMAIL', 'your-email@example.com')
        
        # Cache para el JWT
        self._jwt_token = None
        self._jwt_expiry = None
        
    def _get_jwt_token(self):
        """Genera o retorna el JWT token para autenticación"""
        # Si tenemos un token válido en cache, lo retornamos
        if self._jwt_token and self._jwt_expiry and datetime.now() < self._jwt_expiry:
            return self._jwt_token
            
        try:
            # Payload del JWT
            now = datetime.utcnow()
            exp_time = now + timedelta(hours=1)  # Token válido por 1 hora
            
            payload = {
                'iss': 'UV Alert Vitoria System',
                'iat': int(now.timestamp()),
                'exp': int(exp_time.timestamp()),
                'email': self.api_email
            }
            
            # Generar el JWT con RS256
            token = jwt.encode(
                payload,
                self.private_key,
                algorithm='RS256'
            )
            
            # Guardar en cache
            self._jwt_token = token
            self._jwt_expiry = exp_time - timedelta(minutes=5)  # Renovar 5 min antes
            
            logger.info("JWT token generado exitosamente")
            return token
            
        except Exception as e:
            logger.error(f"Error generando JWT token: {e}")
            return None
    
    def _make_request(self, endpoint, params=None):
        """Hace una petición autenticada a la API"""
        token = self._get_jwt_token()
        if not token:
            return None
            
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error en petición a {endpoint}: {e}")
            return None
    
    def get_current_uv(self):
        """Obtiene el UV actual para Vitoria-Gasteiz"""
        # Primero intentar con endpoint de estaciones UV
        data = self._make_request('weather/stations/uvi/last')
        
        if data:
            # Buscar datos de Vitoria
            for station in data.get('stations', []):
                if 'vitoria' in station.get('name', '').lower():
                    uv_value = station.get('uvi', {}).get('value')
                    if uv_value is not None:
                        logger.info(f"UV obtenido de API: {uv_value}")
                        return float(uv_value)
        
        # Si no hay datos, intentar con endpoint alternativo
        params = {
            'lat': self.vitoria_lat,
            'lon': self.vitoria_lon
        }
        data = self._make_request('weather/uvi/current', params)
        
        if data and 'uvi' in data:
            uv_value = data['uvi']
            logger.info(f"UV obtenido de API (coords): {uv_value}")
            return float(uv_value)
        
        # Si la API falla, usar estimación
        logger.warning("No se pudo obtener UV de la API, usando estimación")
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
        
        return round(estimated_uv, 1)
    
    def get_uv_stations(self):
        """Obtiene lista de estaciones UV"""
        return self._make_request('weather/stations/uvi/list')
    
    def get_forecast(self):
        """Obtiene pronóstico UV"""
        params = {
            'lat': self.vitoria_lat,
            'lon': self.vitoria_lon
        }
        return self._make_request('weather/uvi/forecast', params)