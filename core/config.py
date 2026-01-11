from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from typing import Any, Optional, Dict, List

# ========== ENUMS ==========
class Theme(Enum):
    """Temas disponíveis para a interface"""
    SCI_FI = "sci-fi"
    DARK = "dark"
    LIGHT = "light"
    BLUE_MATRIX = "blue-matrix"
    GREEN_HACKER = "green-hacker"
    CYBERPUNK = "cyberpunk"

class VoiceType(Enum):
    """Tipos de voz disponíveis"""
    OFFLINE = "offline"
    ONLINE = "online"
    HYBRID = "hybrid"

class AlertLevel(Enum):
    """Níveis de alerta"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    SYSTEM = "system"

class Language(Enum):
    """Idiomas suportados"""
    PT_BR = "pt-BR"
    EN_US = "en-US"
    ES_ES = "es-ES"
    FR_FR = "fr-FR"
    DE_DE = "de-DE"

class AIModel(Enum):
    """Modelos de IA suportados"""
    MISTRAL_7B = "mistral-7b"
    GPT_3_5 = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    CLAUDE_3 = "claude-3"
    LOCAL_LLAMA = "llama-2"

# ========== CONFIG CLASS ==========
@dataclass
class AppConfig:
    # Project structure - valores padrão como Path
    PROJECT_ROOT: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    DATA_DIR: Optional[Path] = None
    LOGS_DIR: Optional[Path] = None
    ASSETS_DIR: Optional[Path] = None
    MODELS_DIR: Optional[Path] = None
    PLUGINS_DIR: Optional[Path] = None
    LOCALES_DIR: Optional[Path] = None
    
    # Configuration with defaults
    UI_THEME: Theme = Theme.SCI_FI
    MAX_HISTORY_SIZE: int = 1000
    WINDOW_WIDTH: int = 1600
    WINDOW_HEIGHT: int = 900
    VOICE_MODEL_PATH: Optional[Path] = None
    VOICE_TYPE: VoiceType = VoiceType.HYBRID
    ENABLE_ANALYTICS: bool = True
    ENABLE_TELEMETRY: bool = False

    # API Keys
    WEATHER_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    NOAA_API_KEY: Optional[str] = None

    # AI Settings
    AI_MODEL: AIModel = AIModel.MISTRAL_7B
    AI_MAX_TOKENS: int = 2000
    AI_TEMPERATURE: float = 0.7
    AI_ENABLED: bool = True
    AI_PROVIDER: str = "openrouter"  # openrouter, openai, local

    # Language and voice settings
    LANGUAGE: Language = Language.PT_BR
    VOICE_LANGUAGE: str = "pt"  # Para TTS
    VOICE_GENDER: str = "female"  # ou "male"
    VOICE_SPEED: float = 1.0
    TTS_ENGINE: str = "gtts"  # "gtts" ou "pyttsx3"
    TTS_CACHE: bool = True
    TTS_CACHE_DIR: Optional[Path] = None

    # Voice settings
    VOICE_ACTIVATION_THRESHOLD: float = 0.5
    VOICE_SPEECH_RATE: int = 150
    
    # Paths adicionais
    NOAA_DATA_DIR: Optional[Path] = None
    WEATHER_CACHE_DIR: Optional[Path] = None
    AI_CACHE_DIR: Optional[Path] = None

    # UI settings
    SHOW_NETWORK_MAP: bool = True
    SHOW_ALERT_PANEL: bool = True
    SHOW_MODULE_PANEL: bool = True
    SHOW_AI_PANEL: bool = True
    SHOW_WEATHER_PANEL: bool = True
    SHOW_GESTURE_PANEL: bool = False
    
    # Web Dashboard
    WEB_DASHBOARD_ENABLED: bool = False
    WEB_PORT: int = 8080
    WEB_HOST: str = "localhost"
    WEB_AUTH_REQUIRED: bool = True
    WEB_USERNAME: str = "admin"
    WEB_PASSWORD: str = "admin123"
    
    # Gesture Control
    GESTURE_CONTROL_ENABLED: bool = False
    GESTURE_SENSITIVITY: float = 0.7
    GESTURE_CAMERA_INDEX: int = 0
    
    # Plugin System
    PLUGINS_AUTO_LOAD: bool = True
    PLUGINS_ALLOW_EXTERNAL: bool = False
    PLUGINS_SANDBOX: bool = True
    
    # Module settings
    ENABLE_NOAA: bool = True
    ENABLE_WEATHER: bool = True
    ENABLE_AI: bool = True
    ENABLE_TRADING: bool = False
    ENABLE_MONITORING: bool = True
    ENABLE_SOLAR_MONITOR: bool = True
    ENABLE_VOICE_TTS: bool = True
    ENABLE_WEB_DASHBOARD: bool = False
    ENABLE_GESTURE_CONTROL: bool = False
    
    def __post_init__(self):
        """Post-initialization setup"""
        self._load_config_file()
        self._convert_all_paths()
        self._convert_enums()
        self._set_default_paths()
        self._create_directories()
    
    def _load_config_file(self):
        """Load configuration from JSON file"""
        config_file = self.PROJECT_ROOT / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Atualizar atributos a partir do JSON
                for key, value in config_data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
            except Exception as e:
                print(f"⚠️ Erro ao carregar config.json: {e}")
    
    def _convert_all_paths(self):
        """Converte todos os atributos de caminho para objetos Path"""
        path_attributes = [
            'PROJECT_ROOT', 'DATA_DIR', 'LOGS_DIR', 'ASSETS_DIR',
            'MODELS_DIR', 'VOICE_MODEL_PATH', 'NOAA_DATA_DIR',
            'WEATHER_CACHE_DIR', 'AI_CACHE_DIR', 'PLUGINS_DIR',
            'LOCALES_DIR', 'TTS_CACHE_DIR'
        ]
        
        for attr in path_attributes:
            if hasattr(self, attr):
                value = getattr(self, attr)
                if value is not None and isinstance(value, str):
                    # Se for um caminho relativo, converter para absoluto
                    if attr != 'PROJECT_ROOT' and not os.path.isabs(value):
                        setattr(self, attr, self.PROJECT_ROOT / value)
                    else:
                        setattr(self, attr, Path(value))
    
    def _convert_enums(self):
        """Converte strings para enums, se necessário"""
        enum_mappings = {
            'UI_THEME': Theme,
            'VOICE_TYPE': VoiceType,
            'LANGUAGE': Language,
            'AI_MODEL': AIModel
        }
        
        for attr, enum_class in enum_mappings.items():
            if hasattr(self, attr):
                value = getattr(self, attr)
                if isinstance(value, str):
                    try:
                        setattr(self, attr, enum_class(value))
                    except ValueError:
                        default_value = list(enum_class)[0]
                        print(f"⚠️ {attr} '{value}' inválido. Usando padrão: {default_value.value}")
                        setattr(self, attr, default_value)
    
    def _set_default_paths(self):
        """Define valores padrão para caminhos que podem ser None"""
        defaults = {
            'VOICE_MODEL_PATH': self.MODELS_DIR / "vosk-model-small-pt-0.3",
            'NOAA_DATA_DIR': self.DATA_DIR / "noaa",
            'WEATHER_CACHE_DIR': self.DATA_DIR / "weather_cache",
            'AI_CACHE_DIR': self.DATA_DIR / "ai_cache",
            'TTS_CACHE_DIR': self.DATA_DIR / "tts_cache"
        }
        
        for attr, default_path in defaults.items():
            if getattr(self, attr) is None:
                setattr(self, attr, default_path)
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.DATA_DIR, self.LOGS_DIR, self.ASSETS_DIR,
            self.MODELS_DIR, self.NOAA_DATA_DIR, self.TTS_CACHE_DIR,
            self.WEATHER_CACHE_DIR, self.AI_CACHE_DIR,
            self.PLUGINS_DIR, self.LOCALES_DIR
        ]
        
        for directory in directories:
            if directory is not None:
                directory.mkdir(parents=True, exist_ok=True)
    
    def get_path(self, relative_path: str) -> Path:
        """Helper para obter caminhos relativos ao projeto"""
        return self.PROJECT_ROOT / relative_path
    
    def to_dict(self) -> dict:
        """Converte a configuração para dicionário"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Path):
                result[key] = str(value)
            elif isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result
    
    def save(self):
        """Salva configuração atual em arquivo"""
        config_file = self.PROJECT_ROOT / "config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"✅ Configuração salva em: {config_file}")
        except Exception as e:
            print(f"❌ Erro ao salvar configuração: {e}")
    
    @classmethod
    def load(cls) -> 'AppConfig':
        """Carrega configuração do arquivo"""
        config_file = Path(__file__).parent.parent / "config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return cls(**config_data)
        return cls()