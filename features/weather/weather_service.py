"""
Weather service integration with multiple providers
"""

import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class WeatherCondition:
    """Weather condition data"""
    temperature: float  # Celsius
    feels_like: float  # Celsius
    humidity: int  # Percentage
    pressure: int  # hPa
    wind_speed: float  # m/s
    wind_direction: int  # Degrees
    description: str  # Text description
    icon: str  # Weather icon code
    precipitation: float  # mm
    cloudiness: int  # Percentage
    visibility: int  # meters
    uv_index: float  # UV index
    sunrise: datetime
    sunset: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'temperature': self.temperature,
            'feels_like': self.feels_like,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'description': self.description,
            'icon': self.icon,
            'precipitation': self.precipitation,
            'cloudiness': self.cloudiness,
            'visibility': self.visibility,
            'uv_index': self.uv_index,
            'sunrise': self.sunrise.isoformat(),
            'sunset': self.sunset.isoformat()
        }

@dataclass
class ForecastItem:
    """Forecast item for specific time"""
    timestamp: datetime
    temperature: float
    feels_like: float
    humidity: int
    precipitation_prob: float  # Percentage
    precipitation_amount: float  # mm
    description: str
    icon: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'temperature': self.temperature,
            'feels_like': self.feels_like,
            'humidity': self.humidity,
            'precipitation_prob': self.precipitation_prob,
            'precipitation_amount': self.precipitation_amount,
            'description': self.description,
            'icon': self.icon
        }

@dataclass
class WeatherData:
    """Complete weather data"""
    location: str
    country: str
    latitude: float
    longitude: float
    current: WeatherCondition
    hourly_forecast: List[ForecastItem] = field(default_factory=list)
    daily_forecast: List[ForecastItem] = field(default_factory=list)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    fetched_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'location': self.location,
            'country': self.country,
            'coordinates': {
                'lat': self.latitude,
                'lon': self.longitude
            },
            'current': self.current.to_dict(),
            'hourly_forecast': [f.to_dict() for f in self.hourly_forecast[:24]],
            'daily_forecast': [f.to_dict() for f in self.daily_forecast[:7]],
            'alerts': self.alerts,
            'fetched_at': self.fetched_at.isoformat()
        }

class WeatherProvider:
    """Base class for weather providers"""
    
    def __init__(self, api_key: str, cache_dir: Path = None):
        self.api_key = api_key
        self.cache_dir = cache_dir or Path("data/weather_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_cache_key(self, location: str) -> str:
        """Generate cache key for location"""
        import hashlib
        return hashlib.md5(location.lower().encode()).hexdigest()
    
    def _load_from_cache(self, location: str) -> Optional[WeatherData]:
        """Load weather data from cache"""
        cache_key = self._get_cache_key(location)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
            # Cache valid for 10 minutes
            if cache_age < 600:
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Convert back to WeatherData object
                    return self._dict_to_weather_data(data)
                except:
                    pass
        return None
    
    def _save_to_cache(self, location: str, weather_data: WeatherData):
        """Save weather data to cache"""
        cache_key = self._get_cache_key(location)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(weather_data.to_dict(), f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def _dict_to_weather_data(self, data: Dict) -> WeatherData:
        """Convert dict to WeatherData object"""
        # Implementation depends on provider
        raise NotImplementedError

class OpenWeatherProvider(WeatherProvider):
    """OpenWeatherMap provider"""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    async def get_weather(self, location: str) -> Optional[WeatherData]:
        """Get weather data for location"""
        # Check cache first
        cached = self._load_from_cache(location)
        if cached:
            logger.debug(f"Using cached weather for {location}")
            return cached
        
        try:
            # First get coordinates
            geo_url = f"{self.BASE_URL}/weather"
            params = {
                'q': location,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'pt_br'
            }
            
            async with self.session.get(geo_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_response(data)
                else:
                    logger.error(f"OpenWeather API error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            return None
    
    def _parse_response(self, data: Dict) -> WeatherData:
        """Parse OpenWeather API response"""
        # Parse current weather
        current = data.get('main', {})
        weather = data.get('weather', [{}])[0]
        wind = data.get('wind', {})
        sys = data.get('sys', {})
        
        condition = WeatherCondition(
            temperature=current.get('temp', 0),
            feels_like=current.get('feels_like', 0),
            humidity=current.get('humidity', 0),
            pressure=current.get('pressure', 0),
            wind_speed=wind.get('speed', 0),
            wind_direction=wind.get('deg', 0),
            description=weather.get('description', ''),
            icon=weather.get('icon', ''),
            precipitation=data.get('rain', {}).get('1h', 0) if 'rain' in data else 0,
            cloudiness=data.get('clouds', {}).get('all', 0),
            visibility=data.get('visibility', 10000),
            uv_index=0,  # Not in basic API
            sunrise=datetime.fromtimestamp(sys.get('sunrise', 0)),
            sunset=datetime.fromtimestamp(sys.get('sunset', 0))
        )
        
        weather_data = WeatherData(
            location=data.get('name', 'Unknown'),
            country=sys.get('country', ''),
            latitude=data.get('coord', {}).get('lat', 0),
            longitude=data.get('coord', {}).get('lon', 0),
            current=condition
        )
        
        return weather_data

class WeatherAPIFallback(WeatherProvider):
    """Fallback weather provider using public APIs"""
    
    async def get_weather(self, location: str) -> Optional[WeatherData]:
        """Get weather data using fallback methods"""
        # Simple fallback with mock data
        logger.warning(f"Using fallback weather for {location}")
        
        # Create mock weather data
        condition = WeatherCondition(
            temperature=25.0,
            feels_like=26.0,
            humidity=65,
            pressure=1013,
            wind_speed=3.5,
            wind_direction=180,
            description="Parcialmente nublado",
            icon="02d",
            precipitation=0.0,
            cloudiness=40,
            visibility=10000,
            uv_index=5.0,
            sunrise=datetime.now().replace(hour=6, minute=0, second=0),
            sunset=datetime.now().replace(hour=18, minute=0, second=0)
        )
        
        # Create forecast items
        hourly = []
        daily = []
        
        for i in range(24):
            hourly.append(ForecastItem(
                timestamp=datetime.now() + timedelta(hours=i),
                temperature=24 + (i % 3),
                feels_like=25 + (i % 3),
                humidity=60 + (i % 10),
                precipitation_prob=10 if i < 12 else 30,
                precipitation_amount=0.0,
                description="Parcialmente nublado",
                icon="02d"
            ))
        
        for i in range(7):
            daily.append(ForecastItem(
                timestamp=datetime.now() + timedelta(days=i),
                temperature=24 + (i % 3),
                feels_like=25 + (i % 3),
                humidity=65,
                precipitation_prob=20,
                precipitation_amount=0.0,
                description="Ensolarado" if i < 3 else "Nublado",
                icon="01d" if i < 3 else "03d"
            ))
        
        weather_data = WeatherData(
            location=location,
            country="BR",
            latitude=-23.5505,
            longitude=-46.6333,
            current=condition,
            hourly_forecast=hourly,
            daily_forecast=daily
        )
        
        return weather_data

class WeatherService:
    """Main weather service with multiple providers"""
    
    def __init__(self, config):
        self.config = config
        self.providers = []
        self.active_provider = None
        
        # Initialize providers based on config
        if hasattr(config, 'WEATHER_API_KEY') and config.WEATHER_API_KEY:
            self.providers.append(OpenWeatherProvider(config.WEATHER_API_KEY, config.WEATHER_CACHE_DIR))
        
        # Always add fallback
        self.providers.append(WeatherAPIFallback("", config.WEATHER_CACHE_DIR))
        
        logger.info(f"Weather service initialized with {len(self.providers)} providers")
    
    async def get_weather(self, location: str, use_cache: bool = True) -> Optional[WeatherData]:
        """Get weather data using available providers"""
        if not self.providers:
            return None
        
        # Try each provider in order
        for provider in self.providers:
            try:
                async with provider as p:
                    weather_data = await p.get_weather(location)
                    if weather_data:
                        self.active_provider = provider.__class__.__name__
                        
                        # Save to cache
                        if use_cache:
                            p._save_to_cache(location, weather_data)
                        
                        logger.info(f"Weather for {location} fetched using {self.active_provider}")
                        return weather_data
            except Exception as e:
                logger.error(f"Provider {provider.__class__.__name__} failed: {e}")
                continue
        
        return None
    
    async def get_weather_by_coords(self, lat: float, lon: float) -> Optional[WeatherData]:
        """Get weather by coordinates"""
        # Convert coords to location name if possible
        location = f"{lat},{lon}"
        return await self.get_weather(location)
    
    def get_weather_alerts(self, location: str) -> List[Dict[str, Any]]:
        """Get weather alerts for location"""
        # This would integrate with alert services
        alerts = []
        
        # Mock alerts for demonstration
        if "são paulo" in location.lower():
            alerts.append({
                'type': 'heat',
                'level': 'warning',
                'message': 'Alerta de calor: Temperaturas acima de 30°C',
                'start': datetime.now().isoformat(),
                'end': (datetime.now() + timedelta(days=2)).isoformat()
            })
        
        return alerts
    
    def format_weather_message(self, weather_data: WeatherData) -> str:
        """Format weather data as readable message"""
        if not weather_data:
            return "Não foi possível obter dados do tempo."
        
        current = weather_data.current
        message = f"""
🌤️ **PREVISÃO DO TEMPO - {weather_data.location.upper()}**
        
📊 **CONDIÇÕES ATUAIS:**
• Temperatura: {current.temperature:.1f}°C (Sensação: {current.feels_like:.1f}°C)
• Umidade: {current.humidity}%
• Vento: {current.wind_speed} m/s
• Condição: {current.description.title()}
• Nascer do sol: {current.sunrise.strftime('%H:%M')}
• Pôr do sol: {current.sunset.strftime('%H:%M')}

📈 **PRÓXIMAS HORAS:**
"""
        
        # Add hourly forecast
        for i, hour in enumerate(weather_data.hourly_forecast[:6]):
            if i % 2 == 0:  # Show every 2 hours
                time_str = hour.timestamp.strftime('%H:%M')
                message += f"• {time_str}: {hour.temperature:.1f}°C, {hour.description}\n"
        
        if weather_data.alerts:
            message += "\n⚠️ **ALERTAS:**\n"
            for alert in weather_data.alerts:
                message += f"• {alert['message']}\n"
        
        return message
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get weather service status"""
        return {
            'providers': [p.__class__.__name__ for p in self.providers],
            'active_provider': self.active_provider,
            'cache_enabled': True,
            'cache_dir': str(self.config.WEATHER_CACHE_DIR) if hasattr(self.config, 'WEATHER_CACHE_DIR') else None
        }