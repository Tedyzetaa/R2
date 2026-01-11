"""
Fallback classes for missing modules
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# FALLBACKS PARA MÓDULOS FALTANTES
# ============================================================================

class DummyClass:
    """Classe dummy para qualquer módulo faltante"""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', None)
        print(f"⚠️ Usando DummyClass para {self.__class__.__name__}")
    
    def __getattr__(self, name):
        """Retorna uma função dummy para qualquer método chamado"""
        def dummy_method(*args, **kwargs):
            print(f"⚠️ Método {name} não disponível (DummyClass)")
            return None
        return dummy_method
    
    def __bool__(self):
        return False
    
    def __call__(self, *args, **kwargs):
        return None

# ============================================================================
# FALLBACKS ESPECÍFICOS
# ============================================================================

@dataclass
class SolarWind:
    """Fallback para SolarWind"""
    speed: float = 0.0
    density: float = 0.0
    temperature: float = 0.0
    bz: float = 0.0
    
    @classmethod
    def from_noaa(cls):
        return cls()

class AlertLevel(Enum):
    """Fallback para AlertLevel"""
    NORMAL = "normal"
    WATCH = "watch"
    WARNING = "warning"
    ALERT = "alert"
    SEVERE = "severe"

@dataclass
class Alert:
    """Fallback para Alert"""
    level: AlertLevel = AlertLevel.NORMAL
    message: str = ""
    timestamp: float = 0.0
    
    def to_dict(self):
        return {
            'level': self.level.value,
            'message': self.message,
            'timestamp': self.timestamp
        }

class CommandSystem(DummyClass):
    """Fallback para CommandSystem"""
    def process_command(self, command: str):
        return f"Comando '{command}' recebido (sistema em modo fallback)"

class Analytics(DummyClass):
    """Fallback para Analytics"""
    def record_metric(self, name: str, value: float, tags=None):
        pass
    
    def get_realtime_metrics(self):
        return {
            'health_score': 100.0,
            'status': 'fallback_mode'
        }

class AudioProcessor(DummyClass):
    """Fallback para AudioProcessor"""
    def text_to_speech(self, text: str, blocking=False):
        print(f"🔊 (FALLBACK): {text}")
        return True

class LanguageModel(DummyClass):
    """Fallback para LanguageModel"""
    def get_response(self, prompt: str, **kwargs):
        return type('obj', (object,), {
            'content': f"Estou em modo fallback. Seu prompt: {prompt[:50]}...",
            'model': 'fallback',
            'tokens_used': 0,
            'response_time': 0.1
        })()

class FunctionHandler(DummyClass):
    """Fallback para FunctionHandler"""
    def execute_function(self, name: str, **kwargs):
        return True, f"Função {name} executada (fallback)"

class ModuleManager(DummyClass):
    """Fallback para ModuleManager"""
    def list_modules(self):
        return []
    
    def scan_modules(self):
        return []

# ============================================================================
# FUNÇÕES DE UTILIDADE PARA FALLBACK
# ============================================================================

def safe_import(module_name, class_name, fallback_class):
    """
    Importa uma classe com fallback seguro
    
    Args:
        module_name: Nome do módulo
        class_name: Nome da classe
        fallback_class: Classe de fallback
    
    Returns:
        Classe importada ou fallback
    """
    try:
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        print(f"⚠️ {class_name} não encontrado, usando fallback: {e}")
        return fallback_class

# ============================================================================
# REGISTRO DE FALLBACKS
# ============================================================================

FALLBACK_REGISTRY = {
    'SolarWind': SolarWind,
    'AlertLevel': AlertLevel,
    'Alert': Alert,
    'CommandSystem': CommandSystem,
    'Analytics': Analytics,
    'AudioProcessor': AudioProcessor,
    'LanguageModel': LanguageModel,
    'FunctionHandler': FunctionHandler,
    'ModuleManager': ModuleManager,
}