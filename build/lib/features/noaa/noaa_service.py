"""
NOAA Service - Integração com serviços da NOAA para clima espacial
Serviço profissional para obtenção e processamento de dados solares e geomagnéticos
"""

import requests
import logging
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Níveis de alerta de clima espacial"""
    NORMAL = "normal"
    WATCH = "watch"
    WARNING = "warning"
    ALERT = "alert"
    SEVERE = "severe"

class SolarFlareClass(Enum):
    """Classes de flare solar"""
    A = "A"      # 10^-8 W/m²
    B = "B"      # 10^-7 W/m²
    C = "C"      # 10^-6 W/m²
    M = "M"      # 10^-5 W/m²
    X = "X"      # 10^-4 W/m²
    X_PLUS = "X+" # > 10^-3 W/m²

@dataclass
class SolarFlare:
    """Dados de flare solar"""
    class_value: SolarFlareClass
    peak_time: datetime
    begin_time: datetime
    end_time: datetime
    intensity: float  # W/m²
    location: Optional[Tuple[float, float]] = None  # Coordenadas heliográficas
    active_region: Optional[str] = None
    noaa_scale: AlertLevel = AlertLevel.NORMAL
    effects: List[str] = field(default_factory=list)
    
    @property
    def duration_minutes(self) -> float:
        """Duração do flare em minutos"""
        duration = self.end_time - self.begin_time
        return duration.total_seconds() / 60
    
    @property
    def intensity_log(self) -> float:
        """Intensidade em escala logarítmica"""
        return np.log10(self.intensity * 1e8)  # Normalizado para classe A=1

@dataclass
class GeomagneticStorm:
    """Dados de tempestade geomagnética"""
    kp_index: float  # Índice Kp planetário (0-9)
    g_scale: str  # Escala NOAA G (G1-G5)
    start_time: datetime
    expected_end: datetime
    actual_end: Optional[datetime] = None
    max_kp: float = 0.0
    bz_component: Optional[float] = None  # Componente Bz do campo magnético
    alert_level: AlertLevel = AlertLevel.NORMAL
    estimated_impact: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        """Verifica se a tempestade está ativa"""
        if self.actual_end:
            return datetime.now() < self.actual_end
        return datetime.now() < self.expected_end
    
    @property
    def severity_score(self) -> float:
        """Score de severidade (0-100)"""
        base_score = self.kp_index * 10
        if self.g_scale:
            scale_multiplier = {'G1': 1.0, 'G2': 1.5, 'G3': 2.0, 'G4': 2.5, 'G5': 3.0}
            base_score *= scale_multiplier.get(self.g_scale, 1.0)
        return min(base_score, 100)

@dataclass
class SolarWind:
    """Dados do vento solar"""
    speed: float  # km/s
    density: float  # protons/cm³
    temperature: float  # K
    bz: float  # Componente Bz do campo magnético (nT)
    bt: float  # Magnitude total do campo magnético (nT)
    timestamp: datetime
    source: str = "ACE"  # Advanced Composition Explorer
    
    @property
    def is_geoeffective(self) -> bool:
        """Verifica se o vento solar é geoefetivo"""
        return self.bz < -5 and self.speed > 500  # Condições típicas para tempestades

@dataclass
class SpaceWeatherData:
    """Dados consolidados de clima espacial"""
    timestamp: datetime
    solar_flares: List[SolarFlare]
    geomagnetic_storms: List[GeomagneticStorm]
    solar_wind: SolarWind
    kp_index: float
    aurora_probability: Dict[str, float]  # Probabilidade por região
    electron_flux: float  # Fluxo de elétrons >2MeV
    proton_flux: float  # Fluxo de prótons >10MeV
    xray_flux: Dict[str, float]  # Fluxo de raios-X por banda
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def overall_alert(self) -> AlertLevel:
        """Nível de alerta geral baseado nos dados"""
        levels = []
        
        # Verificar flares X ou M
        for flare in self.solar_flares:
            if flare.class_value in [SolarFlareClass.X, SolarFlareClass.X_PLUS]:
                levels.append(AlertLevel.SEVERE)
            elif flare.class_value == SolarFlareClass.M:
                levels.append(AlertLevel.ALERT)
        
        # Verificar tempestades geomagnéticas
        for storm in self.geomagnetic_storms:
            if storm.kp_index >= 7:
                levels.append(AlertLevel.SEVERE)
            elif storm.kp_index >= 5:
                levels.append(AlertLevel.ALERT)
            elif storm.kp_index >= 4:
                levels.append(AlertLevel.WARNING)
        
        # Determinar nível máximo
        if AlertLevel.SEVERE in levels:
            return AlertLevel.SEVERE
        elif AlertLevel.ALERT in levels:
            return AlertLevel.ALERT
        elif AlertLevel.WARNING in levels:
            return AlertLevel.WARNING
        elif self.kp_index >= 4:
            return AlertLevel.WATCH
        
        return AlertLevel.NORMAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'solar_flares': [
                {
                    'class': flare.class_value.value,
                    'intensity': flare.intensity,
                    'peak_time': flare.peak_time.isoformat(),
                    'duration': flare.duration_minutes
                }
                for flare in self.solar_flares
            ],
            'geomagnetic_storms': [
                {
                    'kp_index': storm.kp_index,
                    'g_scale': storm.g_scale,
                    'is_active': storm.is_active
                }
                for storm in self.geomagnetic_storms
            ],
            'solar_wind': {
                'speed': self.solar_wind.speed,
                'density': self.solar_wind.density,
                'bz': self.solar_wind.bz
            },
            'kp_index': self.kp_index,
            'overall_alert': self.overall_alert.value,
            'electron_flux': self.electron_flux,
            'proton_flux': self.proton_flux
        }

class NOAADataSource(ABC):
    """Interface para fontes de dados da NOAA"""
    
    @abstractmethod
    async def fetch_data(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Busca dados de um endpoint específico"""
        pass
    
    @abstractmethod
    def parse_response(self, data: Dict[str, Any]) -> Any:
        """Parseia a resposta da API"""
        pass

class NOAARESTDataSource(NOAADataSource):
    """Implementação concreta para API REST da NOAA"""
    
    def __init__(self, base_url: str = "https://services.swpc.noaa.gov", timeout: int = 10):
        """
        Inicializa o cliente de dados da NOAA
        
        Args:
            base_url: URL base da API da NOAA
            timeout: Timeout para requisições
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Tuple[datetime, Any]] = {}
        self.cache_ttl = timedelta(minutes=5)
        
    async def __aenter__(self):
        """Context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Obtém dados do cache se válidos"""
        if key in self._cache:
            timestamp, data = self._cache[key]
            if datetime.now() - timestamp < self.cache_ttl:
                return data
        return None
    
    def _set_cached(self, key: str, data: Any):
        """Armazena dados no cache"""
        self._cache[key] = (datetime.now(), data)
    
    async def fetch_data(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Busca dados de um endpoint específico
        
        Args:
            endpoint: Endpoint da API (ex: '/json/ace/swepam.json')
            
        Returns:
            Dados parseados ou None em caso de erro
        """
        # Verificar cache primeiro
        cache_key = f"{self.base_url}{endpoint}"
        cached_data = self._get_cached(cache_key)
        if cached_data:
            logger.debug(f"Usando dados em cache para: {endpoint}")
            return cached_data
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                )
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    self._set_cached(cache_key, data)
                    logger.debug(f"Dados obtidos com sucesso de: {endpoint}")
                    return data
                else:
                    logger.error(f"Erro HTTP {response.status} ao buscar {url}")
                    return None
                    
        except aiohttp.ClientError as e:
            logger.error(f"Erro de conexão ao buscar {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON de {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar {url}: {e}")
            return None
    
    def parse_response(self, data: Dict[str, Any]) -> Any:
        """Parseia a resposta da API (implementação base)"""
        return data

class SolarWindDataSource(NOAARESTDataSource):
    """Fonte de dados específica para vento solar"""
    
    def parse_response(self, data: Dict[str, Any]) -> Optional[SolarWind]:
        """Parseia dados de vento solar"""
        try:
            if not data or 'Data' not in data:
                return None
            
            # Obter dados mais recentes
            latest_data = data['Data'][-1] if data['Data'] else None
            if not latest_data:
                return None
            
            timestamp = datetime.strptime(latest_data[0], "%Y-%m-%d %H:%M:%S.%f")
            
            # Índices do array de dados
            SPEED_INDEX = 1
            DENSITY_INDEX = 2
            TEMPERATURE_INDEX = 3
            BZ_INDEX = 4
            BT_INDEX = 5
            
            return SolarWind(
                speed=float(latest_data[SPEED_INDEX]),
                density=float(latest_data[DENSITY_INDEX]),
                temperature=float(latest_data[TEMPERATURE_INDEX]),
                bz=float(latest_data[BZ_INDEX]),
                bt=float(latest_data[BT_INDEX]),
                timestamp=timestamp
            )
            
        except (IndexError, ValueError, KeyError) as e:
            logger.error(f"Erro ao parsear dados de vento solar: {e}")
            return None

class SolarFlaresDataSource(NOAARESTDataSource):
    """Fonte de dados específica para flares solares"""
    
    def parse_response(self, data: Dict[str, Any]) -> List[SolarFlare]:
        """Parseia dados de flares solares"""
        flares = []
        
        try:
            if not data:
                return flares
            
            # Dados dos últimos 24 horas
            timeframe_hours = 24
            
            for flare_data in data:
                try:
                    # Parsear classe do flare
                    flare_class_str = flare_data.get('classType', '').upper()
                    
                    # Determinar classe
                    flare_class = None
                    if flare_class_str.startswith('X'):
                        flare_class = SolarFlareClass.X
                        if '+' in flare_class_str:
                            flare_class = SolarFlareClass.X_PLUS
                    elif flare_class_str.startswith('M'):
                        flare_class = SolarFlareClass.M
                    elif flare_class_str.startswith('C'):
                        flare_class = SolarFlareClass.C
                    elif flare_class_str.startswith('B'):
                        flare_class = SolarFlareClass.B
                    elif flare_class_str.startswith('A'):
                        flare_class = SolarFlareClass.A
                    
                    if not flare_class:
                        continue
                    
                    # Parsear tempos
                    peak_time = datetime.strptime(
                        flare_data.get('peakTime', ''),
                        "%Y-%m-%dT%H:%M:%SZ"
                    )
                    
                    begin_time = datetime.strptime(
                        flare_data.get('beginTime', ''),
                        "%Y-%m-%dT%H:%M:%SZ"
                    )
                    
                    end_time = datetime.strptime(
                        flare_data.get('endTime', ''),
                        "%Y-%m-%dT%H:%M:%SZ"
                    )
                    
                    # Verificar se está dentro da janela de tempo
                    if datetime.now() - peak_time > timedelta(hours=timeframe_hours):
                        continue
                    
                    # Intensidade
                    intensity = float(flare_data.get('intensity', 0))
                    
                    # Localização (se disponível)
                    location = None
                    if 'location' in flare_data:
                        loc_str = flare_data['location']
                        if loc_str and ':' in loc_str:
                            try:
                                lat, lon = map(float, loc_str.split(':'))
                                location = (lat, lon)
                            except:
                                pass
                    
                    flare = SolarFlare(
                        class_value=flare_class,
                        peak_time=peak_time,
                        begin_time=begin_time,
                        end_time=end_time,
                        intensity=intensity,
                        location=location,
                        active_region=flare_data.get('activeRegion', None),
                        noaa_scale=self._determine_alert_level(flare_class),
                        effects=self._get_flare_effects(flare_class)
                    )
                    
                    flares.append(flare)
                    
                except (ValueError, KeyError) as e:
                    logger.debug(f"Erro ao parsear flare individual: {e}")
                    continue
            
            # Ordenar por intensidade (mais fortes primeiro)
            flares.sort(key=lambda x: x.intensity, reverse=True)
            
        except Exception as e:
            logger.error(f"Erro ao parsear dados de flares: {e}")
        
        return flares
    
    def _determine_alert_level(self, flare_class: SolarFlareClass) -> AlertLevel:
        """Determina nível de alerta baseado na classe do flare"""
        if flare_class in [SolarFlareClass.X, SolarFlareClass.X_PLUS]:
            return AlertLevel.SEVERE
        elif flare_class == SolarFlareClass.M:
            return AlertLevel.ALERT
        elif flare_class == SolarFlareClass.C:
            return AlertLevel.WARNING
        return AlertLevel.NORMAL
    
    def _get_flare_effects(self, flare_class: SolarFlareClass) -> List[str]:
        """Retorna efeitos esperados para cada classe de flare"""
        effects_map = {
            SolarFlareClass.X: [
                "Blackouts de rádio nivel R3-R5",
                "Radiação perigosa para astronautas",
                "Possíveis danos a satélites",
                "Auroras visíveis em baixas latitudes"
            ],
            SolarFlareClass.M: [
                "Blackouts de rádio nivel R1-R2",
                "Tempestades de radiação menores",
                "Perturbações em sistemas de navegação"
            ],
            SolarFlareClass.C: [
                "Blackouts de rádio fracos",
                "Pouco impacto em sistemas terrestres"
            ],
            SolarFlareClass.B: ["Impacto mínimo"],
            SolarFlareClass.A: ["Sem impacto significativo"]
        }
        return effects_map.get(flare_class, [])

class NOAAService:
    """
    Serviço principal de integração com a NOAA
    Gerencia múltiplas fontes de dados e consolida informações
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o serviço NOAA
        
        Args:
            config: Configuração do serviço
        """
        self.config = config or {}
        self.base_url = self.config.get('base_url', 'https://services.swpc.noaa.gov')
        self.timeout = self.config.get('timeout', 15)
        
        # Inicializar fontes de dados
        self.data_sources = {
            'solar_wind': SolarWindDataSource(self.base_url, self.timeout),
            'solar_flares': SolarFlaresDataSource(self.base_url, self.timeout),
            'geomagnetic': NOAARESTDataSource(self.base_url, self.timeout),
            'kp_index': NOAARESTDataSource(self.base_url, self.timeout),
            'aurora': NOAARESTDataSource(self.base_url, self.timeout)
        }
        
        # Cache para dados consolidados
        self._weather_cache: Optional[SpaceWeatherData] = None
        self._last_update: Optional[datetime] = None
        self._update_interval = timedelta(minutes=5)
        
        # Configuração de alertas
        self.alert_callbacks = []
        self.last_alerts = {}
        
        logger.info(f"NOAA Service inicializado com base_url: {self.base_url}")
    
    def register_alert_callback(self, callback):
        """Registra callback para receber alertas"""
        self.alert_callbacks.append(callback)
        logger.debug(f"Callback de alerta registrado: {callback.__name__}")
    
    async def get_space_weather(self, force_update: bool = False) -> Optional[SpaceWeatherData]:
        """
        Obtém dados consolidados de clima espacial
        
        Args:
            force_update: Forçar atualização mesmo com cache válido
            
        Returns:
            SpaceWeatherData ou None em caso de erro
        """
        # Verificar cache
        if not force_update and self._weather_cache and self._last_update:
            if datetime.now() - self._last_update < self._update_interval:
                logger.debug("Retornando dados em cache")
                return self._weather_cache
        
        try:
            # Buscar dados de forma assíncrona
            tasks = [
                self._fetch_solar_wind(),
                self._fetch_solar_flares(),
                self._fetch_geomagnetic_data(),
                self._fetch_kp_index(),
                self._fetch_aurora_data()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Processar resultados
            solar_wind = self._safe_get_result(results[0])
            solar_flares = self._safe_get_result(results[1]) or []
            geomagnetic_storms = self._safe_get_result(results[2]) or []
            kp_index = self._safe_get_result(results[3]) or 0.0
            aurora_data = self._safe_get_result(results[4]) or {}
            
            # Criar objeto consolidado
            weather_data = SpaceWeatherData(
                timestamp=datetime.now(),
                solar_flares=solar_flares,
                geomagnetic_storms=geomagnetic_storms,
                solar_wind=solar_wind or self._create_default_solar_wind(),
                kp_index=kp_index,
                aurora_probability=aurora_data.get('probabilities', {}),
                electron_flux=aurora_data.get('electron_flux', 0.0),
                proton_flux=aurora_data.get('proton_flux', 0.0),
                xray_flux=aurora_data.get('xray_flux', {}),
                alerts=self._generate_alerts(solar_flares, geomagnetic_storms, kp_index)
            )
            
            # Atualizar cache
            self._weather_cache = weather_data
            self._last_update = datetime.now()
            
            # Verificar e enviar alertas
            self._check_and_send_alerts(weather_data)
            
            logger.info(f"Dados de clima espacial atualizados: {weather_data.overall_alert.value}")
            return weather_data
            
        except Exception as e:
            logger.error(f"Erro ao obter dados de clima espacial: {e}")
            return self._weather_cache  # Retornar cache se disponível
    
    def _safe_get_result(self, result):
        """Extrai resultado seguro de tasks com exceções"""
        if isinstance(result, Exception):
            logger.debug(f"Task retornou exceção: {result}")
            return None
        return result
    
    def _create_default_solar_wind(self) -> SolarWind:
        """Cria dados padrão de vento solar"""
        return SolarWind(
            speed=400.0,
            density=5.0,
            temperature=100000.0,
            bz=0.0,
            bt=5.0,
            timestamp=datetime.now()
        )
    
    async def _fetch_solar_wind(self) -> Optional[SolarWind]:
        """Busca dados de vento solar"""
        try:
            async with self.data_sources['solar_wind'] as source:
                data = await source.fetch_data('/json/ace/swepam.json')
                if data:
                    return source.parse_response(data)
        except Exception as e:
            logger.error(f"Erro ao buscar vento solar: {e}")
        return None
    
    async def _fetch_solar_flares(self) -> List[SolarFlare]:
        """Busca dados de flares solares"""
        try:
            async with self.data_sources['solar_flares'] as source:
                data = await source.fetch_data('/json/goes/primary/xray-flares.json')
                if data:
                    return source.parse_response(data)
        except Exception as e:
            logger.error(f"Erro ao buscar flares solares: {e}")
        return []
    
    async def _fetch_geomagnetic_data(self) -> List[GeomagneticStorm]:
        """Busca dados geomagnéticos"""
        try:
            async with self.data_sources['geomagnetic'] as source:
                data = await source.fetch_data('/json/swpc/alerts.json')
                if data:
                    return self._parse_geomagnetic_data(data)
        except Exception as e:
            logger.error(f"Erro ao buscar dados geomagnéticos: {e}")
        return []
    
    async def _fetch_kp_index(self) -> float:
        """Busca índice Kp planetário"""
        try:
            async with self.data_sources['kp_index'] as source:
                data = await source.fetch_data('/products/noaa-planetary-k-index.json')
                if data:
                    return self._parse_kp_index(data)
        except Exception as e:
            logger.error(f"Erro ao buscar índice Kp: {e}")
        return 0.0
    
    async def _fetch_aurora_data(self) -> Dict[str, Any]:
        """Busca dados de aurora"""
        try:
            async with self.data_sources['aurora'] as source:
                data = await source.fetch_data('/json/ovation_aurora_latest.json')
                if data:
                    return self._parse_aurora_data(data)
        except Exception as e:
            logger.error(f"Erro ao buscar dados de aurora: {e}")
        return {}
    
    def _parse_geomagnetic_data(self, data: Dict[str, Any]) -> List[GeomagneticStorm]:
        """Parseia dados de tempestades geomagnéticas"""
        storms = []
        
        try:
            alerts = data.get('alerts', [])
            
            for alert in alerts:
                if alert.get('type') == 'Geomagnetic Storm':
                    try:
                        kp_index = float(alert.get('kp_index', 0))
                        g_scale = alert.get('g_scale', 'G1')
                        
                        # Parsear tempos
                        start_str = alert.get('start_time')
                        end_str = alert.get('expected_end')
                        
                        start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                        expected_end = datetime.fromisoformat(end_str.replace('Z', '+00:00')) if end_str else start_time + timedelta(hours=12)
                        
                        # Determinar nível de alerta
                        alert_level = AlertLevel.NORMAL
                        if kp_index >= 7:
                            alert_level = AlertLevel.SEVERE
                        elif kp_index >= 5:
                            alert_level = AlertLevel.ALERT
                        elif kp_index >= 4:
                            alert_level = AlertLevel.WARNING
                        
                        storm = GeomagneticStorm(
                            kp_index=kp_index,
                            g_scale=g_scale,
                            start_time=start_time,
                            expected_end=expected_end,
                            max_kp=kp_index,
                            bz_component=alert.get('bz', None),
                            alert_level=alert_level,
                            estimated_impact=alert.get('estimated_impact', {})
                        )
                        
                        storms.append(storm)
                        
                    except (ValueError, KeyError) as e:
                        logger.debug(f"Erro ao parsear alerta geomagnético: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"Erro ao parsear dados geomagnéticos: {e}")
        
        return storms
    
    def _parse_kp_index(self, data: Dict[str, Any]) -> float:
        """Parseia índice Kp"""
        try:
            # Tentar obter o valor mais recente
            if 'values' in data and data['values']:
                latest = data['values'][-1]
                if isinstance(latest, dict) and 'kp_index' in latest:
                    return float(latest['kp_index'])
                elif isinstance(latest, (list, tuple)) and len(latest) > 1:
                    return float(latest[1])
        except (ValueError, KeyError, IndexError) as e:
            logger.debug(f"Erro ao parsear índice Kp: {e}")
        
        return 0.0
    
    def _parse_aurora_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parseia dados de aurora"""
        result = {
            'probabilities': {},
            'electron_flux': 0.0,
            'proton_flux': 0.0,
            'xray_flux': {}
        }
        
        try:
            # Probabilidades de aurora por região
            if 'coordinates' in data:
                for coord in data['coordinates']:
                    lat = coord.get('lat', 0)
                    lon = coord.get('lon', 0)
                    prob = coord.get('probability', 0)
                    
                    # Categorizar por latitude
                    if abs(lat) >= 70:
                        region = 'polar'
                    elif abs(lat) >= 60:
                        region = 'auroral'
                    elif abs(lat) >= 50:
                        region = 'mid_latitude'
                    else:
                        region = 'low_latitude'
                    
                    result['probabilities'][region] = max(
                        result['probabilities'].get(region, 0),
                        prob
                    )
            
            # Fluxos de partículas
            if 'electron_flux' in data:
                result['electron_flux'] = float(data['electron_flux'])
            if 'proton_flux' in data:
                result['proton_flux'] = float(data['proton_flux'])
            
            # Fluxo de raios-X
            if 'xray_flux' in data:
                for band, value in data['xray_flux'].items():
                    result['xray_flux'][band] = float(value)
                    
        except Exception as e:
            logger.error(f"Erro ao parsear dados de aurora: {e}")
        
        return result
    
    def _generate_alerts(self, flares: List[SolarFlare], 
                        storms: List[GeomagneticStorm], 
                        kp_index: float) -> List[Dict[str, Any]]:
        """Gera lista de alertas baseada nos dados"""
        alerts = []
        
        # Alertas de flares fortes
        for flare in flares:
            if flare.class_value in [SolarFlareClass.X, SolarFlareClass.X_PLUS]:
                alerts.append({
                    'type': 'solar_flare',
                    'level': 'severe',
                    'message': f'Flare solar classe {flare.class_value.value} detectado',
                    'timestamp': flare.peak_time,
                    'details': {
                        'intensity': flare.intensity,
                        'duration': flare.duration_minutes,
                        'effects': flare.effects
                    }
                })
        
        # Alertas de tempestades geomagnéticas
        for storm in storms:
            if storm.kp_index >= 5:
                alerts.append({
                    'type': 'geomagnetic_storm',
                    'level': 'alert' if storm.kp_index >= 7 else 'warning',
                    'message': f'Tempestade geomagnética {storm.g_scale} em progresso',
                    'timestamp': storm.start_time,
                    'details': {
                        'kp_index': storm.kp_index,
                        'estimated_impact': storm.estimated_impact
                    }
                })
        
        # Alerta de Kp elevado
        if kp_index >= 4:
            alerts.append({
                'type': 'kp_index',
                'level': 'watch',
                'message': f'Índice Kp elevado: {kp_index}',
                'timestamp': datetime.now(),
                'details': {'kp_index': kp_index}
            })
        
        return alerts
    
    def _check_and_send_alerts(self, weather_data: SpaceWeatherData):
        """Verifica e envia alertas se necessário"""
        current_alerts = {}
        
        for alert in weather_data.alerts:
            alert_key = f"{alert['type']}_{alert['timestamp'].timestamp()}"
            current_alerts[alert_key] = alert
            
            # Enviar apenas alertas novos
            if alert_key not in self.last_alerts:
                self._send_alert(alert)
        
        self.last_alerts = current_alerts
    
    def _send_alert(self, alert: Dict[str, Any]):
        """Envia alerta para callbacks registrados"""
        logger.info(f"Enviando alerta: {alert['message']}")
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Erro no callback de alerta {callback.__name__}: {e}")
    
    async def get_historical_data(self, days: int = 7) -> List[SpaceWeatherData]:
        """
        Obtém dados históricos (simulação - em produção usaria API apropriada)
        
        Args:
            days: Número de dias para trás
            
        Returns:
            Lista de dados históricos
        """
        historical = []
        
        try:
            # Simulação de dados históricos
            base_time = datetime.now() - timedelta(days=days)
            
            for i in range(days * 24):  # Horas
                timestamp = base_time + timedelta(hours=i)
                
                # Criar dados simulados
                data = SpaceWeatherData(
                    timestamp=timestamp,
                    solar_flares=[],
                    geomagnetic_storms=[],
                    solar_wind=self._create_default_solar_wind(),
                    kp_index=2.0 + np.random.random() * 2,
                    aurora_probability={'auroral': 0.1},
                    electron_flux=1000 + np.random.random() * 1000,
                    proton_flux=10 + np.random.random() * 10,
                    xray_flux={'0.1-0.8nm': 1e-8, '0.05-0.4nm': 1e-9}
                )
                
                historical.append(data)
            
            logger.info(f"Gerados {len(historical)} registros históricos")
            
        except Exception as e:
            logger.error(f"Erro ao gerar dados históricos: {e}")
        
        return historical
    
    def get_service_status(self) -> Dict[str, Any]:
        """Retorna status do serviço"""
        return {
            'status': 'operational' if self._last_update else 'initializing',
            'last_update': self._last_update.isoformat() if self._last_update else None,
            'cache_age': (datetime.now() - self._last_update).total_seconds() if self._last_update else None,
            'data_sources': list(self.data_sources.keys()),
            'alert_callbacks': len(self.alert_callbacks),
            'config': {
                'base_url': self.base_url,
                'timeout': self.timeout
            }
        }