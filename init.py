"""
R2 Assistant - Sistema de Assistência IA com Interface Sci-Fi/HUD
"""

__version__ = "1.0.0"
__author__ = "R2 Assistant Team"
__license__ = "MIT"
__copyright__ = "Copyright 2024 R2 Assistant Team"

# Imports principais
from .core.config import AppConfig
from .gui.sci_fi_hud import R2SciFiGUI
from .features.alerts import AlertManager, AlertPriority, AlertType
from .features.alerts.notification_system import NotificationSystem, NotificationChannel
from .commands import CommandRegistry, CommandProcessor, CommandContext
from .utils import (
    FileManager, 
    Validator, 
    CacheManager,
    SecurityManager
)

# Exports
__all__ = [
    # Core
    "AppConfig",
    "R2SciFiGUI",
    
    # Features
    "AlertManager",
    "AlertPriority", 
    "AlertType",
    "NotificationSystem", 
    "NotificationChannel",
    
    # Commands
    "CommandRegistry",
    "CommandProcessor", 
    "CommandContext",
    
    # Utils
    "FileManager",
    "Validator",
    "CacheManager", 
    "SecurityManager",
    
    # Metadata
    "__version__",
    "__author__",
    "__license__",
]

# Inicialização
import logging

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Logger principal
logger = logging.getLogger(__name__)
logger.info(f"R2 Assistant v{__version__} inicializado")