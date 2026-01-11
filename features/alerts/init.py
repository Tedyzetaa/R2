"""
Sistema de Alertas e Notificações - Módulo Principal
Gerencia alertas em tempo real e notificações para o sistema HUD Sci-Fi
"""

__version__ = "1.0.0"
__author__ = "R2 Assistant Team"

from .alert_manager import AlertManager, AlertPriority, AlertType
from .notification_system import NotificationSystem, NotificationChannel

__all__ = [
    'AlertManager',
    'AlertPriority',
    'AlertType',
    'NotificationSystem',
    'NotificationChannel'
]