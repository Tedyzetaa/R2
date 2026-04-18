# features/noaa/simple_solar_monitor.py - VERSÃO COMPLETA

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

class AlertLevel(Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class SolarWind:
    """Versão simplificada de SolarWind"""
    speed: float
    density: float
    temperature: float
    timestamp: datetime
    
    @classmethod
    def create_default(cls):
        return cls(
            speed=400.0,
            density=5.0,
            temperature=100000.0,
            timestamp=datetime.now()
        )

class SimpleSolarMonitor:
    """Monitor solar simplificado"""
    
    def __init__(self):
        self.solar_wind = SolarWind.create_default()
    
    def get_status(self):
        return {
            "solar_wind_speed": self.solar_wind.speed,
            "status": "operational"
        }

# ADICIONE ESTAS CLASSES PARA COMPATIBILIDADE:
@dataclass
class SolarFlare:
    """Dummy SolarFlare class"""
    class_value: str = "C"
    intensity: float = 1e-6

@dataclass 
class GeomagneticStorm:
    """Dummy GeomagneticStorm class"""
    kp_index: float = 2.0

@dataclass
class SpaceWeatherData:
    """Dummy SpaceWeatherData class"""
    timestamp: datetime = datetime.now()
    solar_flares: list = None
    geomagnetic_storms: list = None
    solar_wind: SolarWind = None
    kp_index: float = 2.0
    
    def __post_init__(self):
        if self.solar_flares is None:
            self.solar_flares = []
        if self.geomagnetic_storms is None:
            self.geomagnetic_storms = []
        if self.solar_wind is None:
            self.solar_wind = SolarWind.create_default()
    
    def to_dict(self):
        return {
            "kp_index": self.kp_index,
            "solar_wind_speed": self.solar_wind.speed
        }

class SolarMonitor:
    """SolarMonitor simplificado para compatibilidade"""
    def __init__(self, parent, config=None):
        self.parent = parent
        self.config = config or {}
        print("⚠️  SolarMonitor simplificado (sem funcionalidades reais)")
    
    def setup_ui(self):
        print("✅ SolarMonitor UI simplificada")
    
    def start_monitoring(self):
        print("✅ Monitoramento solar simulado iniciado")
    
    def get_monitor_status(self):
        return {"status": "simulado", "message": "Monitor solar simplificado"}

# Export para evitar problemas de importação
__all__ = [
    'SolarWind', 
    'SimpleSolarMonitor', 
    'AlertLevel',
    'SolarMonitor',
    'SolarFlare',
    'GeomagneticStorm', 
    'SpaceWeatherData'
]