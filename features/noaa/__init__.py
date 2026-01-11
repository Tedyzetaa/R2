# features/noaa/__init__.py
"""
NOAA features package
"""
from .noaa_service import (
    NOAAService, 
    SolarWind, 
    SolarFlare, 
    GeomagneticStorm, 
    SpaceWeatherData,
    AlertLevel,
    SolarFlareClass
)

# Só importa o SolarMonitor se houver suporte a interface gráfica
try:
    import tkinter
    from .solar_monitor import SolarMonitor
except (ImportError, ModuleNotFoundError):
    SolarMonitor = None
    print("⚠️ [SISTEMA]: Interface gráfica (Tkinter) não detectada. SolarMonitor desativado.")

__all__ = [
    'NOAAService',
    'SolarWind',
    'SolarFlare',
    'GeomagneticStorm',
    'SpaceWeatherData',
    'AlertLevel',
    'SolarFlareClass',
    'SolarMonitor'
]