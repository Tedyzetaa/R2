"""
Módulo de Trading Automático para R2 Assistant
"""
from .binance_client import BinanceClient
from .trading_engine import TradingEngine

__all__ = ['BinanceClient', 'TradingEngine']