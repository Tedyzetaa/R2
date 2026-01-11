"""
Configuration management for R2 Assistant
"""

import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
from enum import Enum

class VoiceType(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"

class Theme(str, Enum):
    SCI_FI = "sci-fi"
    MATRIX = "matrix"
    CYBERPUNK = "cyberpunk"
    DARK_BLUE = "dark-blue"

@dataclass
class AppConfig:
    """Application configuration with sensible defaults"""
    
    # Project structure
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    ASSETS_DIR: Path = PROJECT_ROOT / "assets"
    SOUNDS_DIR: Path = ASSETS_DIR / "sounds"
    ICONS_DIR: Path = ASSETS_DIR / "icons"
    FONTS_DIR: Path = ASSETS_DIR / "fonts"
    DATA_DIR: Path = PROJECT_ROOT / "data"
    MODULES_FILE: Path = DATA_DIR / "modules.json"
    CACHE_DIR: Path = DATA_DIR / "cache"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    MODELS_DIR: Path = PROJECT_ROOT / "models"
    
    # API Keys (loaded from environment)
    OPENROUTER_API_KEY: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    BINANCE_API_KEY: str = field(default_factory=lambda: os.getenv("BINANCE_API_KEY", ""))
    BINANCE_SECRET_KEY: str = field(default_factory=lambda: os.getenv("BINANCE_SECRET_KEY", ""))
    NEWS_API_KEY: str = field(default_factory=lambda: os.getenv("NEWS_API_KEY", ""))
    WEATHER_API_KEY: str = field(default_factory=lambda: os.getenv("WEATHER_API_KEY", ""))
    
    # Voice configuration
    VOICE_MODEL_PATH: Path = field(default_factory=lambda: Path("models/vosk-model-small-pt-0.3"))
    SAMPLE_RATE: int = 16000
    LANGUAGE: str = "pt-BR"
    VOICE_TYPE: VoiceType = VoiceType.OFFLINE
    VOICE_RATE: int = 150
    VOICE_VOLUME: float = 1.0
    VOICE_PITCH: int = 50
    
    # AI configuration
    AI_MODEL: str = "mistralai/mistral-7b-instruct:free"
    AI_MAX_TOKENS: int = 500
    AI_TEMPERATURE: float = 0.7
    AI_CACHE_SIZE: int = 100
    
    # System configuration
    MAX_HISTORY_SIZE: int = 1000
    API_TIMEOUT: int = 30
    MAX_VOICE_PHRASE_TIME: int = 10
    UPDATE_INTERVAL_MS: int = 100
    
    # UI configuration
    UI_THEME: Theme = Theme.SCI_FI
    UI_SCALING: float = 1.0
    WINDOW_WIDTH: int = 1600
    WINDOW_HEIGHT: int = 900
    
    # Security
    ALLOWED_COMMANDS: List[str] = field(default_factory=lambda: ["python", "conda", "start", "cmd"])
    
    # Trading configuration
    TRADING_ENABLED: bool = False
    RISK_PERCENTAGE: float = 2.0
    TESTNET: bool = True
    
    # Alert configuration
    ALERT_CHECK_INTERVAL: int = 300  # seconds
    ALERT_RETENTION_DAYS: int = 7
    
    # Performance
    ENABLE_CACHING: bool = True
    CACHE_TTL: int = 3600  # seconds
    
    def __post_init__(self):
        """Post-initialization setup"""
        self._create_directories()
        self._load_config_file()
        
        # Convert string paths to Path objects
        if isinstance(self.VOICE_MODEL_PATH, str):
            self.VOICE_MODEL_PATH = Path(self.VOICE_MODEL_PATH)
        
        # Resolve relative paths
        if not self.VOICE_MODEL_PATH.is_absolute():
            self.VOICE_MODEL_PATH = self.PROJECT_ROOT / self.VOICE_MODEL_PATH
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.ASSETS_DIR,
            self.SOUNDS_DIR,
            self.ICONS_DIR,
            self.FONTS_DIR,
            self.DATA_DIR,
            self.CACHE_DIR,
            self.LOGS_DIR,
            self.MODELS_DIR,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_config_file(self):
        """Load additional configuration from config.json"""
        config_file = self.PROJECT_ROOT / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Update configuration from file
                for key, value in config_data.items():
                    key_upper = key.upper()
                    if hasattr(self, key_upper):
                        # Handle enum values
                        if key_upper == 'UI_THEME':
                            value = Theme(value)
                        elif key_upper == 'VOICE_TYPE':
                            value = VoiceType(value)
                        
                        setattr(self, key_upper, value)
                        
            except Exception as e:
                print(f"⚠️ Error loading config.json: {e}")
    
    def save_to_file(self):
        """Save current configuration to config.json"""
        config_file = self.PROJECT_ROOT / "config.json"
        
        # Convert to serializable format
        config_data = {}
        for key in dir(self):
            if not key.startswith('_') and not callable(getattr(self, key)):
                value = getattr(self, key)
                
                # Convert Path objects to strings
                if isinstance(value, Path):
                    value = str(value.relative_to(self.PROJECT_ROOT))
                # Convert enums to their values
                elif isinstance(value, Enum):
                    value = value.value
                
                config_data[key.lower()] = value
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
            return False
    
    @property
    def theme_colors(self) -> Dict[str, str]:
        """Get color scheme for current theme"""
        themes = {
            Theme.SCI_FI: {
                'bg_dark': '#0a0a12',
                'bg_medium': '#10101a',
                'bg_light': '#1a1a2e',
                'primary': '#00ffff',
                'secondary': '#0099ff',
                'accent': '#ff00ff',
                'text': '#ffffff',
                'text_dim': '#8888aa',
                'success': '#00ff88',
                'warning': '#ffaa00',
                'danger': '#ff0066',
            },
            Theme.MATRIX: {
                'bg_dark': '#001100',
                'bg_medium': '#002200',
                'bg_light': '#003300',
                'primary': '#00ff00',
                'secondary': '#00cc00',
                'accent': '#00ff88',
                'text': '#ffffff',
                'text_dim': '#88ff88',
                'success': '#00ff00',
                'warning': '#ffff00',
                'danger': '#ff0000',
            },
            Theme.CYBERPUNK: {
                'bg_dark': '#1a0033',
                'bg_medium': '#2a0044',
                'bg_light': '#3a0055',
                'primary': '#ff00ff',
                'secondary': '#ff00aa',
                'accent': '#00ffff',
                'text': '#ffffff',
                'text_dim': '#cc88ff',
                'success': '#00ff88',
                'warning': '#ffaa00',
                'danger': '#ff0066',
            },
            Theme.DARK_BLUE: {
                'bg_dark': '#0a0a1a',
                'bg_medium': '#10102a',
                'bg_light': '#1a1a3a',
                'primary': '#00aaff',
                'secondary': '#0088ff',
                'accent': '#00ffff',
                'text': '#ffffff',
                'text_dim': '#88aaff',
                'success': '#00ffaa',
                'warning': '#ffaa00',
                'danger': '#ff4444',
            }
        }
        
        return themes.get(self.UI_THEME, themes[Theme.SCI_FI])
    
    @property
    def is_voice_available(self) -> bool:
        """Check if voice features are available"""
        return self.VOICE_TYPE == VoiceType.OFFLINE or (
            self.VOICE_TYPE == VoiceType.ONLINE and self.OPENROUTER_API_KEY
        )
    
    @property
    def is_trading_available(self) -> bool:
        """Check if trading features are available"""
        return self.TRADING_ENABLED and self.BINANCE_API_KEY and self.BINANCE_SECRET_KEY
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check required API keys
        if not self.OPENROUTER_API_KEY:
            issues.append("OPENROUTER_API_KEY is not set")
        
        # Check voice model for offline mode
        if self.VOICE_TYPE == VoiceType.OFFLINE and not self.VOICE_MODEL_PATH.exists():
            issues.append(f"Voice model not found at: {self.VOICE_MODEL_PATH}")
        
        # Check directories
        required_dirs = [self.DATA_DIR, self.CACHE_DIR, self.LOGS_DIR]
        for directory in required_dirs:
            if not directory.exists():
                issues.append(f"Directory does not exist: {directory}")
        
        return issues