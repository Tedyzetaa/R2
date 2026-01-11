"""
Trading Module - Sistema de trading quantitativo do R2 Assistant
Módulo profissional para análise e execução automatizada de trades
"""

from .binance_client import BinanceClient, OrderType, OrderSide, OrderStatus, MarketData
from .trading_engine import TradingEngine, TradingSession, PerformanceMetrics
from .strategies import (
    Strategy, 
    MeanReversionStrategy,
    TrendFollowingStrategy,
    ArbitrageStrategy,
    MLStrategy,
    StrategyFactory
)
from .risk_manager import (
    RiskManager,
    RiskAssessment,
    PositionSizer,
    StopLossManager,
    RiskConfig
)

__all__ = [
    # Binance Client
    'BinanceClient',
    'OrderType',
    'OrderSide', 
    'OrderStatus',
    'MarketData',
    
    # Trading Engine
    'TradingEngine',
    'TradingSession',
    'PerformanceMetrics',
    
    # Strategies
    'Strategy',
    'MeanReversionStrategy',
    'TrendFollowingStrategy',
    'ArbitrageStrategy',
    'MLStrategy',
    'StrategyFactory',
    
    # Risk Management
    'RiskManager',
    'RiskAssessment',
    'PositionSizer',
    'StopLossManager',
    'RiskConfig'
]

# Configuração do módulo
BINANCE_API_BASE = "https://api.binance.com"
BINANCE_WEBSOCKET_BASE = "wss://stream.binance.com:9443"

__version__ = '3.0.0'
__author__ = 'R2 Quantitative Trading Team'
__description__ = 'Sistema profissional de trading quantitativo com gerenciamento de risco'