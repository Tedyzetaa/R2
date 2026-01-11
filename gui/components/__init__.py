"""
Custom UI components for Sci-Fi/HUD interface
"""

from .wave_animation import WaveAnimation
from .circular_gauge import CircularGauge
from .datastream import DataStreamVisualization
from .alert_panel import AlertPanel
from .module_panel import ModulePanel
from .network_map import NetworkMap
from .chat_panel import ChatPanel  # ADICIONAR ESTA LINHA

__all__ = [
    'WaveAnimation',
    'CircularGauge',
    'DataStreamVisualization',
    'AlertPanel',
    'ModulePanel',
    'NetworkMap',
    'ChatPanel'  # ADICIONAR ESTA LINHA
]