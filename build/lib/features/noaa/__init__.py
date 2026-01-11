"""
NOAA Module - Monitoramento de clima espacial e solar
Integração com serviços da NOAA para dados em tempo real
"""

from .noaa_service import NOAAService, SpaceWeatherData, SolarFlare, GeomagneticStorm
from .solar_monitor import SolarMonitor, SolarActivity, SolarWind

__all__ = [
    'NOAAService',
    'SpaceWeatherData',
    'SolarFlare',
    'GeomagneticStorm',
    'SolarMonitor',
    'SolarActivity',
    'SolarWind'
]

# Configuração do módulo NOAA
NOAA_API_BASE = "https://services.swpc.noaa.gov"
NOAA_DATA_SOURCES = {
    'solar_wind': '/json/ace/swepam.json',
    'mag_field': '/json/ace/mag.json',
    'solar_flares': '/json/goes/primary/xray-flares.json',
    'geomagnetic': '/json/swpc/alerts.json',
    'kp_index': '/products/noaa-planetary-k-index.json',
    'aurora': '/json/ovation_aurora_latest.json'
}

__version__ = '2.1.0'
__author__ = 'R2 Space Weather Team'
__description__ = 'Monitoramento de clima espacial e atividade solar em tempo real'