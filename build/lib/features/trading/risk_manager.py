"""
Risk Manager - Sistema avançado de gerenciamento de risco
Controle de exposição, stop loss, position sizing e muito mais
"""

import logging
import math
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd

from .strategies import Signal, SignalType
from .binance_client import OrderSide

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Níveis de risco"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

class PositionSizingMethod(Enum):
    """Métodos de dimensionamento de posição"""
    FIXED = "fixed"  # Posição fixa
    KELLY = "kelly"  # Critério de Kelly
    VOLATILITY = "volatility"  # Baseado na volatilidade
    EQUAL_RISK = "equal_risk"  # Risco igual por trade
    MARTINGALE = "martingale"  # Martingale (cuidado!)

@dataclass
class RiskConfig:
    """Configuração de risco"""
    # Capital e alavancagem
    total_capital: float = 10000.0
    max_capital_usage: float = 0.8  # 80% do capital máximo
    max_leverage: float = 3.0
    
    # Risco por trade
    max_risk_per_trade: float = 0.02  # 2% do capital por trade
    max_daily_loss: float = 0.05  # 5% de perda diária máxima
    max_drawdown: float = 0.15  # 15% de drawdown máximo
    
    # Position sizing
    position_sizing_method: PositionSizingMethod = PositionSizingMethod.EQUAL_RISK
    min_position_size: float = 0.01  # Tamanho mínimo de posição
    max_position_size: float = 0.2  # 20% do capital máximo por posição
    
    # Stop loss e take profit
    default_stop_loss_pct: float = 0.02  # 2% stop loss padrão
    default_take_profit_pct: float = 0.04  # 4% take profit padrão
    trailing_stop_pct: float = 0.01  # 1% trailing stop
    breakeven_stop: bool = True  # Mover stop para breakeven após certo lucro
    
    # Diversificação
    max_positions_per_symbol: int = 1
    max_total_positions: int = 5
    correlation_threshold: float = 0.7  # Limite de correlação entre posições
    
    # Temporal
    max_position_age_hours: int = 48  # Fechar posição após 48 horas
    cool_down_period_minutes: int = 5  # Período de resfriamento entre trades
    
    # Filtros de mercado
    min_volume_usd: float = 1000000  # Volume mínimo de $1M
    max_spread_pct: float = 0.1  # Spread máximo de 0.1%
    volatility_filter: bool = True  # Filtrar por volatilidade
    
    # Regras específicas
    hedge_positions: bool = False  # Permitir hedging
    allow_shorting: bool = True  # Permitir vendas a descoberto
    news_filter: bool = True  # Filtrar trades durante notícias importantes

@dataclass
class RiskAssessment:
    """Avaliação de risco para um trade específico"""
    is_approved: bool = False
    risk_level: RiskLevel = RiskLevel.MODERATE
    risk_score: float = 0.0  # 0-100, onde 0 = sem risco, 100 = risco máximo
    max_position_size: float = 0.0
    recommended_quantity: float = 0.0
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    trailing_stop_percent: float = 0.0
    position_value: float = 0.0
    risk_amount: float = 0.0  # Valor em risco
    reward_risk_ratio: float = 0.0
    expected_value: float = 0.0
    confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'is_approved': self.is_approved,
            'risk_level': self.risk_level.value,
            'risk_score': self.risk_score,
            'max_position_size': self.max_position_size,
            'recommended_quantity': self.recommended_quantity,
            'stop_loss_price': self.stop_loss_price,
            'take_profit_price': self.take_profit_price,
            'trailing_stop_percent': self.trailing_stop_percent,
            'position_value': self.position_value,
            'risk_amount': self.risk_amount,
            'reward_risk_ratio': self.reward_risk_ratio,
            'expected_value': self.expected_value,
            'confidence': self.confidence,
            'reasons': self.reasons,
            'warnings': self.warnings
        }

@dataclass
class PortfolioRisk:
    """Risco total do portfolio"""
    timestamp: datetime
    total_capital: float
    used_capital: float
    available_capital: float
    total_position_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    daily_pnl: float
    daily_pnl_percent: float
    max_drawdown: float
    max_drawdown_percent: float
    var_95: float  # Value at Risk 95%
    expected_shortfall: float
    sharpe_ratio: float
    sortino_ratio: float
    correlation_matrix: Optional[pd.DataFrame] = None
    risk_contributions: Dict[str, float] = field(default_factory=dict)
    
    @property
    def capital_usage_percent(self) -> float:
        """Percentual de uso de capital"""
        if self.total_capital > 0:
            return (self.used_capital / self.total_capital) * 100
        return 0.0

class PositionSizer:
    """Calcula tamanho ótimo de posição baseado em diferentes métodos"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
    
    def calculate_position_size(self, symbol: str, current_price: float,
                              stop_loss_price: float, available_capital: float,
                              method: PositionSizingMethod = None,
                              win_rate: float = 0.5,
                              avg_win_loss_ratio: float = 2.0,
                              volatility: float = 0.02) -> Dict[str, Any]:
        """
        Calcula tamanho de posição ótimo
        
        Args:
            symbol: Símbolo do par
            current_price: Preço atual
            stop_loss_price: Preço de stop loss
            available_capital: Capital disponível
            method: Método de position sizing
            win_rate: Taxa de acerto histórica (0-1)
            avg_win_loss_ratio: Razão média ganho/perda
            volatility: Volatilidade do ativo
            
        Returns:
            Dicionário com resultados
        """
        if method is None:
            method = self.config.position_sizing_method
        
        # Distância do stop loss
        stop_loss_distance = abs(current_price - stop_loss_price) / current_price
        
        if stop_loss_distance == 0:
            stop_loss_distance = self.config.default_stop_loss_pct
        
        results = {
            'method': method.value,
            'stop_loss_distance': stop_loss_distance,
            'available_capital': available_capital
        }
        
        # Calcular baseado no método
        if method == PositionSizingMethod.FIXED:
            size = self._fixed_position_size(available_capital)
        
        elif method == PositionSizingMethod.KELLY:
            size = self._kelly_position_size(available_capital, win_rate, avg_win_loss_ratio)
        
        elif method == PositionSizingMethod.VOLATILITY:
            size = self._volatility_position_size(available_capital, volatility)
        
        elif method == PositionSizingMethod.EQUAL_RISK:
            size = self._equal_risk_position_size(available_capital, stop_loss_distance)
        
        elif method == PositionSizingMethod.MARTINGALE:
            size = self._martingale_position_size(available_capital)
        
        else:
            # Fallback para equal risk
            size = self._equal_risk_position_size(available_capital, stop_loss_distance)
        
        # Aplicar limites
        max_size = available_capital * self.config.max_position_size
        min_size = available_capital * self.config.min_position_size
        
        size = max(min(size, max_size), min_size)
        
        # Calcular quantidade
        if current_price > 0:
            quantity = size / current_price
        else:
            quantity = 0
        
        results.update({
            'position_size': size,
            'quantity': quantity,
            'max_allowed': max_size,
            'min_allowed': min_size,
            'risk_amount': size * stop_loss_distance
        })
        
        return results
    
    def _fixed_position_size(self, available_capital: float) -> float:
        """Posição fixa (ex: 2% do capital)"""
        return available_capital * self.config.max_risk_per_trade
    
    def _kelly_position_size(self, available_capital: float, 
                           win_rate: float, win_loss_ratio: float) -> float:
        """
        Critério de Kelly: f* = p - q/b
        onde p = win rate, q = 1-p, b = win/loss ratio
        """
        if win_loss_ratio <= 0:
            return self._fixed_position_size(available_capital)
        
        kelly_fraction = win_rate - ((1 - win_rate) / win_loss_ratio)
        
        # Kelly fraction ótimo
        kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Limitar a 25%
        
        # Usar metade de Kelly para ser mais conservador
        half_kelly = kelly_fraction / 2
        
        return available_capital * half_kelly
    
    def _volatility_position_size(self, available_capital: float, 
                                volatility: float) -> float:
        """Baseado na volatilidade do ativo"""
        # Ajustar tamanho inversamente à volatilidade
        # Mais volátil = posição menor
        if volatility > 0:
            volatility_factor = 0.02 / volatility  # Normalizar para 2% de volatilidade
            volatility_factor = min(volatility_factor, 2.0)  # Limitar
        else:
            volatility_factor = 1.0
        
        base_size = available_capital * self.config.max_risk_per_trade
        return base_size * volatility_factor
    
    def _equal_risk_position_size(self, available_capital: float,
                                stop_loss_distance: float) -> float:
        """Risco igual por trade"""
        risk_amount = available_capital * self.config.max_risk_per_trade
        
        if stop_loss_distance > 0:
            position_size = risk_amount / stop_loss_distance
        else:
            position_size = risk_amount / self.config.default_stop_loss_pct
        
        return position_size
    
    def _martingale_position_size(self, available_capital: float) -> float:
        """Martingale (apenas para demonstração - NÃO USAR em produção)"""
        # AVISO: Martingale é extremamente arriscado
        logger.warning("Usando método Martingale - EXTREMAMENTE ARRISCADO")
        return available_capital * 0.1  # 10% do capital

class StopLossManager:
    """Gerencia stop losses dinâmicos e trailing stops"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
        self.active_stops: Dict[str, Dict[str, Any]] = {}
    
    def calculate_stop_loss(self, entry_price: float, side: OrderSide,
                          current_price: float, volatility: float = 0.02,
                          atr: float = 0.0) -> Dict[str, Any]:
        """
        Calcula níveis de stop loss ótimos
        
        Args:
            entry_price: Preço de entrada
            side: Lado da posição
            current_price: Preço atual
            volatility: Volatilidade do ativo
            atr: Average True Range
            
        Returns:
            Dicionário com níveis de stop
        """
        # Stop loss baseado em porcentagem fixa
        if side == OrderSide.BUY:
            fixed_stop = entry_price * (1 - self.config.default_stop_loss_pct)
            fixed_take = entry_price * (1 + self.config.default_take_profit_pct)
        else:  # SELL
            fixed_stop = entry_price * (1 + self.config.default_stop_loss_pct)
            fixed_take = entry_price * (1 - self.config.default_take_profit_pct)
        
        # Stop loss baseado em ATR (se disponível)
        if atr > 0:
            atr_multiplier = 2.0  # 2 ATRs
            if side == OrderSide.BUY:
                atr_stop = entry_price - (atr * atr_multiplier)
            else:
                atr_stop = entry_price + (atr * atr_multiplier)
        else:
            atr_stop = fixed_stop
        
        # Stop loss baseado em suporte/resistência (simplificado)
        # Em implementação real, usaríamos análise técnica real
        
        # Escolher o melhor stop loss
        # Para compras, usar o MAIOR entre os stops (mais conservador)
        # Para vendas, usar o MENOR entre os stops
        if side == OrderSide.BUY:
            final_stop = max(fixed_stop, atr_stop)
        else:
            final_stop = min(fixed_stop, atr_stop)
        
        # Garantir que o stop não seja muito apertado
        min_distance = entry_price * 0.005  # Mínimo 0.5%
        if side == OrderSide.BUY:
            if entry_price - final_stop < min_distance:
                final_stop = entry_price - min_distance
        else:
            if final_stop - entry_price < min_distance:
                final_stop = entry_price + min_distance
        
        # Trailing stop
        trailing_stop = None
        if self.config.trailing_stop_pct > 0:
            trailing_stop = self.config.trailing_stop_pct
        
        # Breakeven stop
        breakeven_level = None
        if self.config.breakeven_stop:
            breakeven_profit = 0.01  # 1% de lucro
            if side == OrderSide.BUY:
                breakeven_level = entry_price * (1 + breakeven_profit)
            else:
                breakeven_level = entry_price * (1 - breakeven_profit)
        
        return {
            'fixed_stop': fixed_stop,
            'atr_stop': atr_stop if atr > 0 else None,
            'final_stop': final_stop,
            'take_profit': fixed_take,
            'trailing_stop_percent': trailing_stop,
            'breakeven_level': breakeven_level,
            'stop_distance_percent': abs(entry_price - final_stop) / entry_price * 100,
            'reward_risk_ratio': abs(fixed_take - entry_price) / abs(entry_price - final_stop)
        }
    
    def update_trailing_stop(self, symbol: str, current_price: float,
                           side: OrderSide, trailing_percent: float) -> Optional[float]:
        """
        Atualiza trailing stop baseado no preço atual
        
        Args:
            symbol: Símbolo da posição
            current_price: Preço atual
            side: Lado da posição
            trailing_percent: Percentual do trailing stop
            
        Returns:
            Novo nível de stop ou None se não atualizado
        """
        if symbol not in self.active_stops:
            return None
        
        stop_info = self.active_stops[symbol]
        current_stop = stop_info['current_stop']
        best_price = stop_info['best_price']
        
        # Atualizar melhor preço
        if side == OrderSide.BUY:
            if current_price > best_price:
                stop_info['best_price'] = current_price
                # Calcular novo stop
                new_stop = current_price * (1 - trailing_percent)
                if new_stop > current_stop:
                    stop_info['current_stop'] = new_stop
                    return new_stop
        else:  # SELL
            if current_price < best_price:
                stop_info['best_price'] = current_price
                new_stop = current_price * (1 + trailing_percent)
                if new_stop < current_stop:
                    stop_info['current_stop'] = new_stop
                    return new_stop
        
        return None
    
    def register_stop(self, symbol: str, entry_price: float, 
                     stop_loss: float, side: OrderSide):
        """Registra um novo stop loss"""
        self.active_stops[symbol] = {
            'entry_price': entry_price,
            'current_stop': stop_loss,
            'best_price': entry_price,
            'side': side,
            'registered_at': datetime.now()
        }
    
    def remove_stop(self, symbol: str):
        """Remove stop loss registrado"""
        if symbol in self.active_stops:
            del self.active_stops[symbol]

class RiskManager:
    """
    Gerenciador de risco principal
    Avalia e controla todos os aspectos de risco do trading
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o gerenciador de risco
        
        Args:
            config: Configuração de risco
        """
        self.config = RiskConfig(**(config or {}))
        self.position_sizer = PositionSizer(self.config)
        self.stop_loss_manager = StopLossManager(self.config)
        
        # Histórico de trades
        self.trade_history: List[Dict[str, Any]] = []
        self.daily_pnl: List[Tuple[datetime, float]] = []
        
        # Limites atuais
        self.daily_loss = 0.0
        self.max_drawdown = 0.0
        self.current_drawdown = 0.0
        self.peak_capital = self.config.total_capital
        
        # Estado
        self.cool_down_until: Optional[datetime] = None
        self.is_cool_down = False
        
        # Filtros de mercado
        self.market_conditions: Dict[str, Any] = {}
        
        logger.info("Risk Manager inicializado")
    
    def assess_trade(self, symbol: str, signal: Signal, current_price: float,
                    positions: Dict[str, Any], capital: float) -> RiskAssessment:
        """
        Avalia risco de um trade específico
        
        Args:
            symbol: Símbolo do par
            signal: Sinal de trading
            current_price: Preço atual
            positions: Posições atuais
            capital: Capital disponível
            
        Returns:
            Avaliação de risco detalhada
        """
        assessment = RiskAssessment()
        
        # 1. Verificar condições básicas
        if not self._check_basic_conditions(symbol, current_price, assessment):
            return assessment
        
        # 2. Verificar limites do portfolio
        if not self._check_portfolio_limits(symbol, positions, capital, assessment):
            return assessment
        
        # 3. Verificar condições de mercado
        if not self._check_market_conditions(symbol, current_price, assessment):
            return assessment
        
        # 4. Verificar limites diários
        if not self._check_daily_limits(assessment):
            return assessment
        
        # 5. Calcular parâmetros do trade
        trade_params = self._calculate_trade_parameters(
            symbol, signal, current_price, capital
        )
        
        # 6. Aplicar position sizing
        position_size = self._apply_position_sizing(
            symbol, current_price, trade_params['stop_loss'], capital, assessment
        )
        
        if position_size['quantity'] <= 0:
            assessment.is_approved = False
            assessment.reasons.append("Tamanho de posição inválido")
            return assessment
        
        # 7. Calcular métricas de risco
        self._calculate_risk_metrics(
            symbol, signal, current_price, position_size, trade_params, assessment
        )
        
        # 8. Avaliação final
        assessment.is_approved = self._final_assessment(assessment)
        
        return assessment
    
    def _check_basic_conditions(self, symbol: str, current_price: float,
                              assessment: RiskAssessment) -> bool:
        """Verifica condições básicas para trading"""
        reasons = []
        
        # Preço válido
        if current_price <= 0:
            reasons.append("Preço inválido")
            return False
        
        # Símbolo válido
        if not symbol or len(symbol) < 3:
            reasons.append("Símbolo inválido")
            return False
        
        # Cool down period
        if self.is_cool_down and self.cool_down_until:
            if datetime.now() < self.cool_down_until:
                reasons.append(f"Período de resfriamento até {self.cool_down_until}")
                return False
        
        assessment.reasons.extend(reasons)
        return True
    
    def _check_portfolio_limits(self, symbol: str, positions: Dict[str, Any],
                              capital: float, assessment: RiskAssessment) -> bool:
        """Verifica limites do portfolio"""
        reasons = []
        
        # Limite de posições por símbolo
        if symbol in positions:
            if self.config.max_positions_per_symbol <= 1:
                reasons.append(f"Já existe posição aberta em {symbol}")
                return False
        
        # Limite total de posições
        if len(positions) >= self.config.max_total_positions:
            reasons.append(f"Número máximo de posições atingido ({self.config.max_total_positions})")
            return False
        
        # Uso de capital
        total_position_value = sum(
            p.quantity * p.current_price for p in positions.values()
        )
        
        capital_usage = total_position_value / capital
        if capital_usage > self.config.max_capital_usage:
            reasons.append(f"Uso de capital excedido ({capital_usage:.1%}/{self.config.max_capital_usage:.1%})")
            return False
        
        assessment.reasons.extend(reasons)
        return True
    
    def _check_market_conditions(self, symbol: str, current_price: float,
                               assessment: RiskAssessment) -> bool:
        """Verifica condições de mercado"""
        reasons = []
        
        # Em implementação real, buscaríamos dados de mercado
        # Aqui são verificações simplificadas
        
        # Volume mínimo (simulado)
        if self.config.min_volume_usd > 0:
            # Simulando volume - em produção buscar da API
            simulated_volume = 5000000  # $5M
            if simulated_volume < self.config.min_volume_usd:
                reasons.append(f"Volume insuficiente (${simulated_volume:,.0f})")
                return False
        
        # Spread (simulado)
        if self.config.max_spread_pct > 0:
            simulated_spread = 0.05  # 0.05%
            if simulated_spread > self.config.max_spread_pct:
                reasons.append(f"Spread muito alto ({simulated_spread:.2%})")
                return False
        
        # Filtro de notícias (simulado)
        if self.config.news_filter:
            # Em produção, integrar com feed de notícias
            has_important_news = False  # Simulação
            if has_important_news:
                reasons.append("Notícias importantes em andamento")
                return False
        
        assessment.reasons.extend(reasons)
        return True
    
    def _check_daily_limits(self, assessment: RiskAssessment) -> bool:
        """Verifica limites diários"""
        reasons = []
        
        # Perda diária
        if self.daily_loss < -abs(self.config.max_daily_loss * self.config.total_capital):
            reasons.append(f"Perda diária limite atingida (${self.daily_loss:,.2f})")
            return False
        
        # Drawdown
        current_capital = self.config.total_capital + sum(
            p.unrealized_pnl for p in self._get_all_positions_simulated()
        )
        
        if current_capital > self.peak_capital:
            self.peak_capital = current_capital
        
        self.current_drawdown = (self.peak_capital - current_capital) / self.peak_capital
        
        if self.current_drawdown > self.config.max_drawdown:
            reasons.append(f"Drawdown máximo excedido ({self.current_drawdown:.1%})")
            return False
        
        assessment.reasons.extend(reasons)
        return True
    
    def _get_all_positions_simulated(self) -> List[Any]:
        """Obtém todas as posições (simulado para demonstração)"""
        # Em produção, obter do trading engine
        return []
    
    def _calculate_trade_parameters(self, symbol: str, signal: Signal,
                                  current_price: float, capital: float) -> Dict[str, Any]:
        """Calcula parâmetros do trade"""
        # Determinar side baseado no sinal
        if signal.strength > 0:
            side = OrderSide.BUY
        else:
            side = OrderSide.SELL
        
        # Calcular stop loss e take profit
        stop_params = self.stop_loss_manager.calculate_stop_loss(
            entry_price=current_price,
            side=side,
            current_price=current_price,
            volatility=0.02,  # Simulado
            atr=current_price * 0.02  # Simulado
        )
        
        return {
            'side': side,
            'stop_loss': stop_params['final_stop'],
            'take_profit': stop_params['take_profit'],
            'trailing_stop': stop_params['trailing_stop_percent'],
            'reward_risk_ratio': stop_params['reward_risk_ratio'],
            'stop_distance_percent': stop_params['stop_distance_percent']
        }
    
    def _apply_position_sizing(self, symbol: str, current_price: float,
                              stop_loss: float, capital: float,
                              assessment: RiskAssessment) -> Dict[str, Any]:
        """Aplica position sizing"""
        # Calcular distância do stop loss
        stop_distance = abs(current_price - stop_loss) / current_price
        
        # Obter métricas históricas (simuladas)
        win_rate = 0.55  # Simulado
        avg_win_loss_ratio = 2.0  # Simulado
        volatility = 0.02  # Simulado
        
        # Calcular tamanho de posição
        position_size = self.position_sizer.calculate_position_size(
            symbol=symbol,
            current_price=current_price,
            stop_loss_price=stop_loss,
            available_capital=capital,
            win_rate=win_rate,
            avg_win_loss_ratio=avg_win_loss_ratio,
            volatility=volatility
        )
        
        assessment.max_position_size = position_size['max_allowed']
        assessment.recommended_quantity = position_size['quantity']
        assessment.position_value = position_size['position_size']
        assessment.risk_amount = position_size['risk_amount']
        
        return position_size
    
    def _calculate_risk_metrics(self, symbol: str, signal: Signal,
                              current_price: float, position_size: Dict[str, Any],
                              trade_params: Dict[str, Any], assessment: RiskAssessment):
        """Calcula métricas de risco detalhadas"""
        # Score de risco baseado em múltiplos fatores
        risk_score = 0.0
        
        # 1. Força do sinal (20%)
        signal_strength_factor = abs(signal.strength)
        risk_score += (1 - signal_strength_factor) * 20
        
        # 2. Confiança da estratégia (20%)
        confidence_factor = signal.confidence
        risk_score += (1 - confidence_factor) * 20
        
        # 3. Tamanho da posição (30%)
        position_size_ratio = position_size['position_size'] / self.config.total_capital
        size_factor = min(position_size_ratio / self.config.max_position_size, 1.0)
        risk_score += size_factor * 30
        
        # 4. Volatilidade (15%)
        volatility_factor = 0.02 / 0.05  # Normalizado para 5% de volatilidade
        volatility_factor = min(volatility_factor, 1.0)
        risk_score += volatility_factor * 15
        
        # 5. Condições de mercado (15%)
        market_factor = 0.5  # Simulado
        risk_score += market_factor * 15
        
        assessment.risk_score = risk_score
        
        # Determinar nível de risco
        if risk_score < 20:
            assessment.risk_level = RiskLevel.VERY_LOW
        elif risk_score < 40:
            assessment.risk_level = RiskLevel.LOW
        elif risk_score < 60:
            assessment.risk_level = RiskLevel.MODERATE
        elif risk_score < 80:
            assessment.risk_level = RiskLevel.HIGH
        else:
            assessment.risk_level = RiskLevel.VERY_HIGH
        
        # Outras métricas
        assessment.stop_loss_price = trade_params['stop_loss']
        assessment.take_profit_price = trade_params['take_profit']
        assessment.trailing_stop_percent = trade_params['trailing_stop']
        assessment.reward_risk_ratio = trade_params['reward_risk_ratio']
        assessment.confidence = signal.confidence
        
        # Expected Value (simplificado)
        win_probability = 0.55  # Simulado
        loss_probability = 1 - win_probability
        avg_win = trade_params['reward_risk_ratio'] * assessment.risk_amount
        avg_loss = assessment.risk_amount
        
        assessment.expected_value = (win_probability * avg_win) - (loss_probability * avg_loss)
    
    def _final_assessment(self, assessment: RiskAssessment) -> bool:
        """Avaliação final do trade"""
        reasons_to_approve = []
        reasons_to_reject = []
        
        # Critérios de aprovação
        if assessment.risk_score > 70:
            reasons_to_reject.append(f"Score de risco muito alto: {assessment.risk_score:.1f}")
        
        if assessment.reward_risk_ratio < 1.5:
            reasons_to_reject.append(f"Ratio recompensa/risco baixo: {assessment.reward_risk_ratio:.2f}")
        
        if assessment.expected_value < 0:
            reasons_to_reject.append(f"Valor esperado negativo: ${assessment.expected_value:.2f}")
        
        if assessment.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            reasons_to_reject.append(f"Nível de risco {assessment.risk_level.value}")
        
        # Critérios de aprovação positiva
        if assessment.reward_risk_ratio > 3.0:
            reasons_to_approve.append(f"Excelente ratio recompensa/risco: {assessment.reward_risk_ratio:.2f}")
        
        if assessment.risk_score < 30:
            reasons_to_approve.append(f"Baixo score de risco: {assessment.risk_score:.1f}")
        
        if assessment.confidence > 0.8:
            reasons_to_approve.append(f"Alta confiança: {assessment.confidence:.0%}")
        
        # Decisão final
        if reasons_to_reject:
            assessment.is_approved = False
            assessment.warnings.extend(reasons_to_reject)
        elif reasons_to_approve or assessment.risk_level in [RiskLevel.VERY_LOW, RiskLevel.LOW, RiskLevel.MODERATE]:
            assessment.is_approved = True
            assessment.reasons.extend(reasons_to_approve)
        else:
            assessment.is_approved = False
            assessment.warnings.append("Avaliação inconclusiva")
        
        return assessment.is_approved
    
    def update_trade_result(self, symbol: str, pnl: float, commission: float):
        """Atualiza resultados de um trade concluído"""
        trade_result = {
            'symbol': symbol,
            'pnl': pnl,
            'commission': commission,
            'timestamp': datetime.now(),
            'net_pnl': pnl - commission
        }
        
        self.trade_history.append(trade_result)
        
        # Atualizar perda diária
        self.daily_loss += pnl - commission
        
        # Reiniciar daily loss no próximo dia
        if len(self.daily_pnl) > 0:
            last_date = self.daily_pnl[-1][0].date()
            if datetime.now().date() > last_date:
                self.daily_loss = 0
        
        self.daily_pnl.append((datetime.now(), pnl - commission))
        
        # Ativar cool down se perda significativa
        if pnl < 0 and abs(pnl) > self.config.total_capital * 0.01:
            self.activate_cool_down()
    
    def activate_cool_down(self, minutes: Optional[int] = None):
        """Ativa período de resfriamento"""
        if minutes is None:
            minutes = self.config.cool_down_period_minutes
        
        self.cool_down_until = datetime.now() + timedelta(minutes=minutes)
        self.is_cool_down = True
        
        logger.info(f"Período de resfriamento ativado por {minutes} minutos")
    
    def deactivate_cool_down(self):
        """Desativa período de resfriamento"""
        self.cool_down_until = None
        self.is_cool_down = False
        
        logger.info("Período de resfriamento desativado")
    
    def calculate_portfolio_risk(self, positions: Dict[str, Any],
                               current_prices: Dict[str, float]) -> PortfolioRisk:
        """Calcula risco total do portfolio"""
        total_value = 0
        unrealized_pnl = 0
        
        position_values = {}
        
        for symbol, position in positions.items():
            current_price = current_prices.get(symbol, position.current_price)
            position_value = position.quantity * current_price
            position_pnl = position.unrealized_pnl
            
            total_value += position_value
            unrealized_pnl += position_pnl
            position_values[symbol] = position_value
        
        # Calcular VaR (Value at Risk) - simplificado
        # Em produção, usaríamos métodos mais sofisticados
        var_95 = total_value * 0.05  # 5% VaR simplificado
        expected_shortfall = var_95 * 1.3  # ES é geralmente maior que VaR
        
        # Calcular métricas de performance
        returns = [trade['net_pnl'] for trade in self.trade_history[-100:]] if self.trade_history else [0]
        
        if len(returns) > 1:
            returns_array = np.array(returns)
            mean_return = returns_array.mean()
            std_return = returns_array.std()
            
            if std_return > 0:
                sharpe = (mean_return / std_return) * np.sqrt(252)
                
                # Sortino ratio (usando apenas retornos negativos)
                negative_returns = returns_array[returns_array < 0]
                if len(negative_returns) > 0 and negative_returns.std() > 0:
                    sortino = (mean_return / negative_returns.std()) * np.sqrt(252)
                else:
                    sortino = 0
            else:
                sharpe = 0
                sortino = 0
        else:
            sharpe = 0
            sortino = 0
        
        # Calcular contribuição de risco (simplificado)
        risk_contributions = {}
        for symbol, value in position_values.items():
            if total_value > 0:
                risk_contributions[symbol] = (value / total_value) * 100
        
        return PortfolioRisk(
            timestamp=datetime.now(),
            total_capital=self.config.total_capital,
            used_capital=total_value,
            available_capital=self.config.total_capital - total_value,
            total_position_value=total_value,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=(unrealized_pnl / self.config.total_capital) * 100,
            daily_pnl=self.daily_loss,
            daily_pnl_percent=(self.daily_loss / self.config.total_capital) * 100,
            max_drawdown=self.max_drawdown,
            max_drawdown_percent=self.max_drawdown * 100,
            var_95=var_95,
            expected_shortfall=expected_shortfall,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            risk_contributions=risk_contributions
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do risk manager"""
        return {
            'config': {
                'total_capital': self.config.total_capital,
                'max_risk_per_trade': self.config.max_risk_per_trade,
                'max_daily_loss': self.config.max_daily_loss,
                'max_drawdown': self.config.max_drawdown
            },
            'current_state': {
                'daily_loss': self.daily_loss,
                'current_drawdown': self.current_drawdown,
                'peak_capital': self.peak_capital,
                'is_cool_down': self.is_cool_down,
                'cool_down_until': self.cool_down_until.isoformat() if self.cool_down_until else None
            },
            'statistics': {
                'total_trades': len(self.trade_history),
                'winning_trades': len([t for t in self.trade_history if t['net_pnl'] > 0]),
                'losing_trades': len([t for t in self.trade_history if t['net_pnl'] < 0]),
                'total_pnl': sum(t['net_pnl'] for t in self.trade_history) if self.trade_history else 0,
                'largest_win': max([t['net_pnl'] for t in self.trade_history], default=0),
                'largest_loss': min([t['net_pnl'] for t in self.trade_history], default=0)
            },
            'position_sizing_method': self.config.position_sizing_method.value
        }