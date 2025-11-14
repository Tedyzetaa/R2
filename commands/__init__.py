"""
Comandos do R2 Assistant
"""
from .system_commands import register_system_commands
from .web_commands import register_web_commands
from .basic_commands import register_basic_commands
from .crypto_commands import register_crypto_commands

__all__ = [
    'register_system_commands',
    'register_web_commands', 
    'register_basic_commands',
    'register_crypto_commands'
]