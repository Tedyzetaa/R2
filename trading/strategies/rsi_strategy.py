from .base_strategy import BaseStrategy
from trading.indicators.rsi import calculate_rsi
from typing import Dict, Any

class RSIStrategy(BaseStrategy):
    """Estratégia RSI Overbought/Oversold"""
    
    def __init__(self, rsi_period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__("RSI Strategy")
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.is_opened = False
        
    def should_buy(self, data: Dict[str, Any]) -> bool:
        """Compra quando RSI está oversold"""
        if not data.get('prices'):
            return False
            
        rsi = calculate_rsi(data['prices'], self.rsi_period)
        return rsi is not None and rsi < self.oversold and not self.is_opened
    
    def should_sell(self, data: Dict[str, Any]) -> bool:
        """Vende quando RSI está overbought"""
        if not data.get('prices'):
            return False
            
        rsi = calculate_rsi(data['prices'], self.rsi_period)
        return rsi is not None and rsi > self.overbought and self.is_opened
    
    def set_position_status(self, opened: bool):
        """Atualiza status da posição"""
        self.is_opened = opened