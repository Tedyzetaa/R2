#!/usr/bin/env python3
"""
NOAA Service - Monitoramento de Clima Espacial
Versão: 2.1.0
Autor: R2 Assistant Team
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    WARNING = "WARNING"
    ALERT = "ALERT"
    SEVERE = "SEVERE"

class SolarFlareClass(Enum):
    A = "A"
    B = "B"
    C = "C"
    M = "M"
    X = "X"
    X_PLUS = "X+"

@dataclass
class SolarFlare:
    class_value: SolarFlareClass
    peak_time: datetime
    intensity: float
    active_region: str = ""
    duration_minutes: float = 0.0
    noaa_scale: AlertLevel = AlertLevel.NORMAL
    effects: List[str] = field(default_factory=list)

@dataclass
class SolarWind:
    speed: float  # km/s
    density: float  # p/cm³
    temperature: float  # K
    bz: float  # nT (componente Bz)
    bt: float  # nT (magnitude total)
    timestamp: datetime

@dataclass
class GeomagneticStorm:
    level: str  # G1-G5
    kp_index: float
    dst_index: float
    start_time: datetime
    expected_end: Optional[datetime] = None
    noaa_scale: AlertLevel = AlertLevel.NORMAL

@dataclass
class SpaceWeatherData:
    timestamp: datetime
    solar_flares: List[SolarFlare] = field(default_factory=list)
    geomagnetic_storms: List[GeomagneticStorm] = field(default_factory=list)
    solar_wind: Optional[SolarWind] = None
    coronal_mass_ejections: List[Dict] = field(default_factory=list)
    proton_events: List[Dict] = field(default_factory=list)
    kp_index: float = 0.0
    dst_index: float = 0.0
    aurora_probability: Dict[str, float] = field(default_factory=dict)
    sunspot_number: int = 0
    solar_flux: float = 0.0
    alerts: List[Dict] = field(default_factory=list)
    overall_alert: AlertLevel = AlertLevel.NORMAL

class NOAAService:
    """Serviço principal para monitoramento NOAA"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Any] = {}
        self.last_update: Optional[datetime] = None
        self.current_data: Optional[SpaceWeatherData] = None
        self.is_running = False
        
        # Endpoints NOAA
        self.endpoints = {
            "solar_wind": "https://services.swpc.noaa.gov/json/ace/swepam.json",
            "geomagnetic_indices": "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
            "solar_flares": "https://services.swpc.noaa.gov/json/goes/primary/xray-flares.json",
            "cme_data": "https://services.swpc.noaa.gov/json/llsdat.json",
            "proton_flux": "https://services.swpc.noaa.gov/json/goes/proton-flux.json",
            "aurora_forecast": "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json",
            "sunspot_regions": "https://services.swpc.noaa.gov/json/solar-cycle/sunspots.json"
        }
        
        logger.info("NOAA Service inicializado")
    
    def _load_config(self, config_path: str) -> Dict:
        """Carrega configuração do arquivo"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return {
                "noaa_update_interval": 300,
                "cache_ttl": 300,
                "alert_thresholds": {
                    "solar_flare": ["M", "X", "X+"],
                    "kp_index": 6.0,
                    "solar_wind_speed": 600
                }
            }
    
    async def start(self):
        """Inicia o serviço NOAA"""
        if self.is_running:
            return
        
        self.session = aiohttp.ClientSession()
        self.is_running = True
        
        # Primeira atualização
        await self.update_all_data()
        
        logger.info("NOAA Service iniciado")
    
    async def stop(self):
        """Para o serviço NOAA"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.session:
            await self.session.close()
        
        logger.info("NOAA Service parado")
    
    async def fetch_data(self, endpoint: str) -> Optional[Dict]:
        """Busca dados de um endpoint NOAA"""
        if not self.session:
            return None
        
        try:
            async with self.session.get(endpoint, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Erro {response.status} ao buscar {endpoint}")
                    return None
        except Exception as e:
            logger.error(f"Erro ao buscar {endpoint}: {e}")
            return None
    
    async def update_solar_wind(self):
        """Atualiza dados do vento solar"""
        data = await self.fetch_data(self.endpoints["solar_wind"])
        if data and len(data) > 0:
            latest = data[-1]
            try:
                solar_wind = SolarWind(
                    speed=float(latest.get("speed", 0)),
                    density=float(latest.get("density", 0)),
                    temperature=float(latest.get("temperature", 0)),
                    bz=float(latest.get("bz", 0)),
                    bt=float(latest.get("bt", 0)),
                    timestamp=datetime.strptime(latest.get("time_tag", ""), "%Y-%m-%d %H:%M:%S.%f")
                )
                return solar_wind
            except (ValueError, KeyError) as e:
                logger.error(f"Erro ao processar vento solar: {e}")
        
        return None
    
    async def update_kp_index(self):
        """Atualiza índice Kp"""
        data = await self.fetch_data(self.endpoints["geomagnetic_indices"])
        if data and len(data) > 0:
            # Pega o último valor válido
            for item in reversed(data):
                try:
                    if len(item) >= 2:
                        kp_value = float(item[1])
                        if kp_value >= 0:
                            return kp_value
                except (ValueError, IndexError):
                    continue
        
        return 0.0
    
    async def update_all_data(self):
        """Atualiza todos os dados NOAA"""
        logger.info("Atualizando dados NOAA...")
        
        # Atualiza dados em paralelo
        tasks = [
            self.update_solar_wind(),
            self.update_kp_index(),
            # Outras atualizações aqui
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa resultados
        solar_wind = results[0] if not isinstance(results[0], Exception) else None
        kp_index = results[1] if not isinstance(results[1], Exception) else 0.0
        
        # Cria objeto de dados
        self.current_data = SpaceWeatherData(
            timestamp=datetime.now(),
            solar_wind=solar_wind,
            kp_index=kp_index,
            overall_alert=self._calculate_alert_level(kp_index, solar_wind)
        )
        
        self.last_update = datetime.now()
        logger.info(f"Dados NOAA atualizados: Kp={kp_index}, Vento Solar={'OK' if solar_wind else 'N/A'}")
        
        return self.current_data
    
    def _calculate_alert_level(self, kp_index: float, solar_wind: Optional[SolarWind]) -> AlertLevel:
        """Calcula nível de alerta baseado nos dados"""
        if kp_index >= 8.0:
            return AlertLevel.SEVERE
        elif kp_index >= 6.0:
            return AlertLevel.ALERT
        elif kp_index >= 5.0:
            return AlertLevel.WARNING
        elif kp_index >= 4.0:
            return AlertLevel.WATCH
        else:
            return AlertLevel.NORMAL
    
    def get_summary(self) -> Dict:
        """Retorna resumo dos dados atuais"""
        if not self.current_data:
            return {"status": "no_data", "message": "Nenhum dado disponível"}
        
        summary = {
            "status": "ok",
            "timestamp": self.current_data.timestamp.isoformat(),
            "kp_index": self.current_data.kp_index,
            "overall_alert": self.current_data.overall_alert.value,
            "solar_wind": {
                "speed": self.current_data.solar_wind.speed if self.current_data.solar_wind else 0,
                "density": self.current_data.solar_wind.density if self.current_data.solar_wind else 0,
                "bz": self.current_data.solar_wind.bz if self.current_data.solar_wind else 0
            } if self.current_data.solar_wind else None,
            "alerts": self.current_data.alerts
        }
        
        return summary

# Instância global do serviço
_noaa_service = None

def get_noaa_service() -> NOAAService:
    """Retorna instância global do serviço NOAA"""
    global _noaa_service
    if _noaa_service is None:
        _noaa_service = NOAAService()
    return _noaa_service

async def main_test():
    """Função de teste principal"""
    service = get_noaa_service()
    await service.start()
    
    try:
        # Aguarda um pouco para dados serem carregados
        await asyncio.sleep(2)
        
        # Obtém resumo
        summary = service.get_summary()
        print("Resumo NOAA:", json.dumps(summary, indent=2))
        
    finally:
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main_test())
