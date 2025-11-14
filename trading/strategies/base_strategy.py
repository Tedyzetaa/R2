from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseStrategy(ABC):
    """Classe base para estratégias de trading"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_active = False
        
    @abstractmethod
    def should_buy(self, data: Dict[str, Any]) -> bool:
        """Determina se deve comprar"""
        pass
    
    @abstractmethod
    def should_sell(self, data: Dict[str, Any]) -> bool:
        """Determina se deve vender"""
        pass
    
    def update_parameters(self, **kwargs):
        """Atualiza parâmetros da estratégia"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)