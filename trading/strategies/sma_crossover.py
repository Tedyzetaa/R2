from .base_strategy import BaseStrategy
from trading.indicators.sma import calculate_sma
from typing import Dict, Any, List

class SMACrossoverStrategy(BaseStrategy):
    """Estratégia SMA Crossover - Conversão do JavaScript para Python"""
    
    def __init__(self, short_period: int = 13, long_period: int = 21):
        super().__init__("SMA Crossover")
        self.short_period = short_period
        self.long_period = long_period
        self.is_opened = False
        
    def should_buy(self, data: Dict[str, Any]) -> bool:
        """Condição de compra: SMA curta cruza SMA longa para cima"""
        if not data.get('prices') or len(data['prices']) < self.long_period:
            return False
            
        prices = data['prices']
        sma_short = calculate_sma(prices, self.short_period)
        sma_long = calculate_sma(prices, self.long_period)
        
        if sma_short is None or sma_long is None:
            return False
            
        # SMA13 > SMA21 E não temos posição aberta
        return sma_short > sma_long and not self.is_opened
    
    def should_sell(self, data: Dict[str, Any]) -> bool:
        """Condição de venda: SMA curta cruza SMA longa para baixo"""
        if not data.get('prices') or len(data['prices']) < self.long_period:
            return False
            
        prices = data['prices']
        sma_short = calculate_sma(prices, self.short_period)
        sma_long = calculate_sma(prices, self.long_period)
        
        if sma_short is None or sma_long is None:
            return False
            
        # SMA13 < SMA21 E temos posição aberta
        return sma_short < sma_long and self.is_opened
    
    def set_position_status(self, opened: bool):
        """Atualiza status da posição"""
        self.is_opened = opened