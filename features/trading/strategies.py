"""
Trading Strategies - Estratégias de trading quantitativo
Implementações de várias estratégias para diferentes mercados e condições
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import talib
from abc import ABC, abstractmethod

from .binance_client import MarketData, OrderSide

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Tipos de sinal de trading"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    EXIT = "exit"

@dataclass
class Signal:
    """Sinal de trading gerado por uma estratégia"""
    type: SignalType
    strength: float  # -1.0 a 1.0, onde negativo = venda, positivo = compra
    confidence: float  # 0.0 a 1.0
    price: float
    timestamp: datetime
    symbol: str
    indicators: Dict[str, float] = field(default_factory=dict)
    rationale: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'type': self.type.value,
            'strength': self.strength,
            'confidence': self.confidence,
            'price': self.price,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'rationale': self.rationale,
            'indicators': self.indicators
        }

class Strategy(ABC):
    """
    Classe base abstrata para todas as estratégias de trading
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa a estratégia
        
        Args:
            name: Nome da estratégia
            config: Configuração específica da estratégia
        """
        self.name = name
        self.config = config or {}
        self.parameters = self._set_default_parameters()
        self.parameters.update(self.config.get('parameters', {}))
        
        # Estado da estratégia
        self.position = 0  # -1 (short), 0 (neutral), 1 (long)
        self.last_signal: Optional[Signal] = None
        self.signals_generated = 0
        
        # Dados históricos
        self.historical_data: Optional[pd.DataFrame] = None
        
        logger.info(f"Estratégia '{name}' inicializada")
    
    def _set_default_parameters(self) -> Dict[str, Any]:
        """Define parâmetros padrão da estratégia"""
        return {
            'enabled': True,
            'timeframe': '1h',
            'max_position': 1.0,
            'stop_loss_pct': 2.0,
            'take_profit_pct': 4.0,
            'trailing_stop_pct': 1.5
        }
    
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores técnicos para os dados"""
        pass
    
    @abstractmethod
    def generate_signal(self, symbol: str, current_price: float,
                       market_data: Optional[MarketData] = None,
                       historical_data: Optional[pd.DataFrame] = None,
                       positions: Optional[Dict[str, Any]] = None) -> Optional[Signal]:
        """
        Gera sinal de trading baseado na estratégia
        
        Args:
            symbol: Símbolo do par
            current_price: Preço atual
            market_data: Dados de mercado em tempo real
            historical_data: Dados históricos
            positions: Posições atuais
            
        Returns:
            Signal ou None se nenhum sinal
        """
        pass
    
    def initialize(self, historical_data: pd.DataFrame):
        """Inicializa estratégia com dados históricos"""
        self.historical_data = historical_data.copy()
        
        if len(historical_data) > 0:
            # Calcular indicadores iniciais
            self.historical_data = self.calculate_indicators(self.historical_data)
        
        logger.debug(f"Estratégia '{self.name}' inicializada com {len(historical_data)} registros")
    
    def update(self, new_data: pd.DataFrame):
        """Atualiza estratégia com novos dados"""
        if self.historical_data is None:
            self.historical_data = new_data.copy()
        else:
            self.historical_data = pd.concat([self.historical_data, new_data])
        
        # Recalcular indicadores
        self.historical_data = self.calculate_indicators(self.historical_data)
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status da estratégia"""
        return {
            'name': self.name,
            'position': self.position,
            'signals_generated': self.signals_generated,
            'last_signal': self.last_signal.to_dict() if self.last_signal else None,
            'parameters': self.parameters,
            'enabled': self.parameters.get('enabled', True)
        }

class MeanReversionStrategy(Strategy):
    """
    Estratégia de Mean Reversion (Reversão à Média)
    Baseada em Bollinger Bands e RSI
    """
    
    def _set_default_parameters(self) -> Dict[str, Any]:
        """Parâmetros específicos para Mean Reversion"""
        params = super()._set_default_parameters()
        params.update({
            'bb_period': 20,
            'bb_std': 2.0,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'volume_threshold': 1.5,
            'min_touch_bands': 2
        })
        return params
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores para Mean Reversion"""
        df = data.copy()
        
        # Bollinger Bands
        bb_period = self.parameters['bb_period']
        bb_std = self.parameters['bb_std']
        
        df['bb_middle'] = df['close'].rolling(window=bb_period).mean()
        df['bb_std'] = df['close'].rolling(window=bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * bb_std)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * bb_std)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # RSI
        rsi_period = self.parameters['rsi_period']
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Volume médio
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Percentual de distância das bands
        df['dist_to_upper'] = (df['close'] - df['bb_upper']) / df['bb_middle'] * 100
        df['dist_to_lower'] = (df['close'] - df['bb_lower']) / df['bb_middle'] * 100
        
        # Contador de toques nas bands
        df['touch_upper'] = df['close'] >= df['bb_upper']
        df['touch_lower'] = df['close'] <= df['bb_lower']
        
        return df
    
    def generate_signal(self, symbol: str, current_price: float,
                       market_data: Optional[MarketData] = None,
                       historical_data: Optional[pd.DataFrame] = None,
                       positions: Optional[Dict[str, Any]] = None) -> Optional[Signal]:
        """Gera sinal baseado em Mean Reversion"""
        if historical_data is None or len(historical_data) < 50:
            return None
        
        # Obter últimos dados
        df = historical_data.iloc[-50:].copy()
        
        if len(df) < 20:
            return None
        
        # Calcular indicadores se necessário
        if 'bb_upper' not in df.columns:
            df = self.calculate_indicators(df)
        
        # Últimos valores
        last_close = df['close'].iloc[-1]
        last_rsi = df['rsi'].iloc[-1]
        last_dist_lower = df['dist_to_lower'].iloc[-1]
        last_dist_upper = df['dist_to_upper'].iloc[-1]
        last_volume_ratio = df['volume_ratio'].iloc[-1]
        
        # Contar toques recentes nas bands
        recent_touches_upper = df['touch_upper'].tail(10).sum()
        recent_touches_lower = df['touch_lower'].tail(10).sum()
        
        signal = None
        rationale_parts = []
        
        # Condições de COMPRA (oversold)
        buy_conditions = []
        buy_strength = 0.0
        
        # 1. Preço abaixo da banda inferior
        if last_dist_lower < 0:
            buy_conditions.append(f"Preço {abs(last_dist_lower):.1f}% abaixo da BB inferior")
            buy_strength += 0.3
        
        # 2. RSI oversold
        if last_rsi < self.parameters['rsi_oversold']:
            buy_conditions.append(f"RSI oversold ({last_rsi:.1f})")
            buy_strength += 0.3
        
        # 3. Volume acima da média
        if last_volume_ratio > self.parameters['volume_threshold']:
            buy_conditions.append(f"Volume {last_volume_ratio:.1f}x acima da média")
            buy_strength += 0.2
        
        # 4. Múltiplos toques na banda inferior
        if recent_touches_lower >= self.parameters['min_touch_bands']:
            buy_conditions.append(f"{recent_touches_lower} toques recentes na BB inferior")
            buy_strength += 0.2
        
        # Condições de VENDA (overbought)
        sell_conditions = []
        sell_strength = 0.0
        
        # 1. Preço acima da banda superior
        if last_dist_upper > 0:
            sell_conditions.append(f"Preço {last_dist_upper:.1f}% acima da BB superior")
            sell_strength += 0.3
        
        # 2. RSI overbought
        if last_rsi > self.parameters['rsi_overbought']:
            sell_conditions.append(f"RSI overbought ({last_rsi:.1f})")
            sell_strength += 0.3
        
        # 3. Volume acima da média
        if last_volume_ratio > self.parameters['volume_threshold']:
            sell_conditions.append(f"Volume {last_volume_ratio:.1f}x acima da média")
            sell_strength += 0.2
        
        # 4. Múltiplos toques na banda superior
        if recent_touches_upper >= self.parameters['min_touch_bands']:
            sell_conditions.append(f"{recent_touches_upper} toques recentes na BB superior")
            sell_strength += 0.2
        
        # Determinar sinal final
        confidence = 0.0
        
        if buy_strength > 0.5 and buy_strength > sell_strength:
            signal_type = SignalType.BUY
            strength = min(buy_strength, 1.0)
            confidence = buy_strength
            rationale = " | ".join(buy_conditions)
            
            # Ajustar força baseado na distância da banda
            if last_dist_lower < -5:
                strength = min(strength * 1.2, 1.0)
        
        elif sell_strength > 0.5 and sell_strength > buy_strength:
            signal_type = SignalType.SELL
            strength = -min(sell_strength, 1.0)  # Negativo para venda
            confidence = sell_strength
            rationale = " | ".join(sell_conditions)
            
            # Ajustar força baseado na distância da banda
            if last_dist_upper > 5:
                strength = max(strength * 1.2, -1.0)
        
        else:
            # Sem sinal claro
            signal_type = SignalType.HOLD
            strength = 0.0
            confidence = max(buy_strength, sell_strength) / 2
            rationale = "Condições inconclusivas"
        
        # Criar sinal
        if strength != 0 or signal_type == SignalType.HOLD:
            signal = Signal(
                type=signal_type,
                strength=strength,
                confidence=confidence,
                price=current_price,
                timestamp=datetime.now(),
                symbol=symbol,
                indicators={
                    'rsi': last_rsi,
                    'bb_dist_lower': last_dist_lower,
                    'bb_dist_upper': last_dist_upper,
                    'volume_ratio': last_volume_ratio,
                    'bb_width': df['bb_width'].iloc[-1]
                },
                rationale=rationale
            )
            
            self.last_signal = signal
            self.signals_generated += 1
            
            # Atualizar posição
            if signal_type == SignalType.BUY:
                self.position = 1
            elif signal_type == SignalType.SELL:
                self.position = -1
            elif signal_type == SignalType.EXIT:
                self.position = 0
        
        return signal

class TrendFollowingStrategy(Strategy):
    """
    Estratégia de Trend Following (Seguimento de Tendência)
    Baseada em Médias Móveis, MACD e ADX
    """
    
    def _set_default_parameters(self) -> Dict[str, Any]:
        """Parâmetros específicos para Trend Following"""
        params = super()._set_default_parameters()
        params.update({
            'fast_ma': 9,
            'slow_ma': 21,
            'signal_ma': 50,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'adx_period': 14,
            'adx_threshold': 25,
            'atr_period': 14,
            'atr_multiplier': 2.0,
            'trend_confirmation_bars': 3
        })
        return params
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores para Trend Following"""
        df = data.copy()
        
        # Médias Móveis
        df['ma_fast'] = df['close'].rolling(window=self.parameters['fast_ma']).mean()
        df['ma_slow'] = df['close'].rolling(window=self.parameters['slow_ma']).mean()
        df['ma_signal'] = df['close'].rolling(window=self.parameters['signal_ma']).mean()
        
        # MACD
        macd_fast = self.parameters['macd_fast']
        macd_slow = self.parameters['macd_slow']
        macd_signal = self.parameters['macd_signal']
        
        exp1 = df['close'].ewm(span=macd_fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=macd_slow, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=macd_signal, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # ADX (Directional Movement Index)
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range
        df['tr'] = np.maximum(
            high - low,
            np.maximum(
                abs(high - close.shift()),
                abs(low - close.shift())
            )
        )
        
        # Directional Movement
        up_move = high - high.shift()
        down_move = low.shift() - low
        
        pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Smoothed DM
        df['pos_dm'] = pd.Series(pos_dm).ewm(alpha=1/self.parameters['adx_period'], adjust=False).mean()
        df['neg_dm'] = pd.Series(neg_dm).ewm(alpha=1/self.parameters['adx_period'], adjust=False).mean()
        
        # Smoothed TR
        df['atr'] = df['tr'].ewm(alpha=1/self.parameters['adx_period'], adjust=False).mean()
        
        # Directional Indicators
        df['plus_di'] = 100 * (df['pos_dm'] / df['atr'])
        df['minus_di'] = 100 * (df['neg_dm'] / df['atr'])
        
        # ADX
        dx = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
        df['adx'] = dx.ewm(alpha=1/self.parameters['adx_period'], adjust=False).mean()
        
        # ATR para stop loss
        df['atr'] = df['tr'].rolling(window=self.parameters['atr_period']).mean()
        
        # Tendência
        df['trend'] = np.where(
            df['ma_fast'] > df['ma_slow'], 1,
            np.where(df['ma_fast'] < df['ma_slow'], -1, 0)
        )
        
        # Confirmação de tendência
        df['trend_confirmed'] = df['trend'].rolling(
            window=self.parameters['trend_confirmation_bars']
        ).apply(lambda x: 1 if all(x > 0) else (-1 if all(x < 0) else 0))
        
        return df
    
    def generate_signal(self, symbol: str, current_price: float,
                       market_data: Optional[MarketData] = None,
                       historical_data: Optional[pd.DataFrame] = None,
                       positions: Optional[Dict[str, Any]] = None) -> Optional[Signal]:
        """Gera sinal baseado em Trend Following"""
        if historical_data is None or len(historical_data) < 100:
            return None
        
        df = historical_data.iloc[-100:].copy()
        
        if len(df) < 50:
            return None
        
        # Calcular indicadores se necessário
        if 'ma_fast' not in df.columns:
            df = self.calculate_indicators(df)
        
        # Últimos valores
        last_close = df['close'].iloc[-1]
        last_ma_fast = df['ma_fast'].iloc[-1]
        last_ma_slow = df['ma_slow'].iloc[-1]
        last_ma_signal = df['ma_signal'].iloc[-1]
        last_macd = df['macd'].iloc[-1]
        last_macd_signal = df['macd_signal'].iloc[-1]
        last_macd_hist = df['macd_hist'].iloc[-1]
        last_adx = df['adx'].iloc[-1]
        last_plus_di = df['plus_di'].iloc[-1]
        last_minus_di = df['minus_di'].iloc[-1]
        last_trend_confirmed = df['trend_confirmed'].iloc[-1]
        
        # Histórico recente
        recent_macd_hist = df['macd_hist'].tail(5).values
        recent_trend = df['trend'].tail(5).values
        
        signal = None
        rationale_parts = []
        
        # Determinar tendência predominante
        is_uptrend = last_trend_confirmed > 0
        is_downtrend = last_trend_confirmed < 0
        strong_trend = last_adx > self.parameters['adx_threshold']
        
        # Sinal de COMPRA (tendência de alta)
        buy_conditions = []
        buy_strength = 0.0
        
        if is_uptrend:
            buy_conditions.append(f"Tendência de alta confirmada")
            buy_strength += 0.3
            
            if strong_trend:
                buy_conditions.append(f"Tendência forte (ADX: {last_adx:.1f})")
                buy_strength += 0.2
            
            # MA fast acima da slow
            if last_ma_fast > last_ma_slow:
                buy_conditions.append(f"MA{self.parameters['fast_ma']} > MA{self.parameters['slow_ma']}")
                buy_strength += 0.2
            
            # MACD acima do sinal
            if last_macd > last_macd_signal:
                buy_conditions.append("MACD > Signal")
                buy_strength += 0.2
            
            # MACD histogram positivo e crescendo
            if last_macd_hist > 0 and len(recent_macd_hist) >= 2:
                if recent_macd_hist[-1] > recent_macd_hist[-2]:
                    buy_conditions.append("MACD histogram crescendo")
                    buy_strength += 0.1
            
            # +DI > -DI
            if last_plus_di > last_minus_di:
                buy_conditions.append(f"+DI > -DI ({last_plus_di:.1f} > {last_minus_di:.1f})")
                buy_strength += 0.1
        
        # Sinal de VENDA (tendência de baixa)
        sell_conditions = []
        sell_strength = 0.0
        
        if is_downtrend:
            sell_conditions.append(f"Tendência de baixa confirmada")
            sell_strength += 0.3
            
            if strong_trend:
                sell_conditions.append(f"Tendência forte (ADX: {last_adx:.1f})")
                sell_strength += 0.2
            
            # MA fast abaixo da slow
            if last_ma_fast < last_ma_slow:
                sell_conditions.append(f"MA{self.parameters['fast_ma']} < MA{self.parameters['slow_ma']}")
                sell_strength += 0.2
            
            # MACD abaixo do sinal
            if last_macd < last_macd_signal:
                sell_conditions.append("MACD < Signal")
                sell_strength += 0.2
            
            # MACD histogram negativo e decrescendo
            if last_macd_hist < 0 and len(recent_macd_hist) >= 2:
                if recent_macd_hist[-1] < recent_macd_hist[-2]:
                    sell_conditions.append("MACD histogram decrescendo")
                    sell_strength += 0.1
            
            # -DI > +DI
            if last_minus_di > last_plus_di:
                sell_conditions.append(f"-DI > +DI ({last_minus_di:.1f} > {last_plus_di:.1f})")
                sell_strength += 0.1
        
        # Determinar sinal final
        confidence = 0.0
        
        if buy_strength > 0.6 and buy_strength > sell_strength:
            signal_type = SignalType.BUY
            strength = min(buy_strength, 1.0)
            confidence = buy_strength
            rationale = " | ".join(buy_conditions)
            
            # Ajustar força baseado na força da tendência
            if strong_trend:
                strength = min(strength * 1.3, 1.0)
        
        elif sell_strength > 0.6 and sell_strength > buy_strength:
            signal_type = SignalType.SELL
            strength = -min(sell_strength, 1.0)
            confidence = sell_strength
            rationale = " | ".join(sell_conditions)
            
            # Ajustar força baseado na força da tendência
            if strong_trend:
                strength = max(strength * 1.3, -1.0)
        
        else:
            # Sinal de EXIT se tendência enfraquecendo
            if self.position != 0 and last_adx < self.parameters['adx_threshold'] / 2:
                signal_type = SignalType.EXIT
                strength = 0.0
                confidence = 0.7
                rationale = f"Tendência enfraquecendo (ADX: {last_adx:.1f})"
            else:
                signal_type = SignalType.HOLD
                strength = 0.0
                confidence = max(buy_strength, sell_strength) / 2
                rationale = "Tendência indefinida ou fraca"
        
        # Criar sinal
        if strength != 0 or signal_type in [SignalType.HOLD, SignalType.EXIT]:
            signal = Signal(
                type=signal_type,
                strength=strength,
                confidence=confidence,
                price=current_price,
                timestamp=datetime.now(),
                symbol=symbol,
                indicators={
                    'ma_fast': last_ma_fast,
                    'ma_slow': last_ma_slow,
                    'macd': last_macd,
                    'macd_signal': last_macd_signal,
                    'macd_hist': last_macd_hist,
                    'adx': last_adx,
                    'plus_di': last_plus_di,
                    'minus_di': last_minus_di,
                    'atr': df['atr'].iloc[-1]
                },
                rationale=rationale
            )
            
            self.last_signal = signal
            self.signals_generated += 1
            
            # Atualizar posição
            if signal_type == SignalType.BUY:
                self.position = 1
            elif signal_type == SignalType.SELL:
                self.position = -1
            elif signal_type == SignalType.EXIT:
                self.position = 0
        
        return signal

class ArbitrageStrategy(Strategy):
    """
    Estratégia de Arbitragem Triangular
    Explora diferenças de preço entre múltiplos pares
    """
    
    def _set_default_parameters(self) -> Dict[str, Any]:
        """Parâmetros específicos para Arbitragem"""
        params = super()._set_default_parameters()
        params.update({
            'min_profit_pct': 0.5,
            'max_position_time': 300,  # segundos
            'slippage_pct': 0.1,
            'fee_pct': 0.1,
            'volume_threshold': 0.1,
            'triangles': [
                ['BTC', 'USDT', 'ETH'],  # BTC/USDT -> ETH/BTC -> ETH/USDT
                ['ETH', 'USDT', 'BNB'],  # ETH/USDT -> BNB/ETH -> BNB/USDT
            ]
        })
        return params
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Para arbitragem, não calculamos indicadores tradicionais"""
        return data
    
    def find_arbitrage_opportunities(self, prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Encontra oportunidades de arbitragem triangular
        
        Args:
            prices: Dicionário de preços {par: preço}
            
        Returns:
            Lista de oportunidades encontradas
        """
        opportunities = []
        triangles = self.parameters['triangles']
        min_profit = self.parameters['min_profit_pct']
        slippage = self.parameters['slippage_pct']
        fee = self.parameters['fee_pct']
        
        for triangle in triangles:
            if len(triangle) != 3:
                continue
            
            a, b, c = triangle
            
            # Construir pares
            pairs = [
                f"{a}{b}", f"{b}{a}",
                f"{b}{c}", f"{c}{b}",
                f"{a}{c}", f"{c}{a}"
            ]
            
            # Verificar se temos preços para todos os pares necessários
            required_pairs = [f"{a}{b}", f"{b}{c}", f"{c}{a}"]
            if all(p in prices for p in required_pairs):
                # Calcular arbitragem direta
                start_amount = 1.0
                
                # Passo 1: A -> B
                rate1 = prices[f"{a}{b}"]
                amount1 = start_amount * rate1 * (1 - fee/100)
                
                # Passo 2: B -> C
                rate2 = prices[f"{b}{c}"]
                amount2 = amount1 * rate2 * (1 - fee/100)
                
                # Passo 3: C -> A
                rate3 = prices[f"{c}{a}"]
                final_amount = amount2 * rate3 * (1 - fee/100)
                
                # Calcular lucro
                profit_pct = (final_amount - start_amount) / start_amount * 100
                
                # Ajustar por slippage
                net_profit = profit_pct - (slippage * 3)
                
                if net_profit > min_profit:
                    opportunities.append({
                        'triangle': triangle,
                        'path': [f"{a}{b}", f"{b}{c}", f"{c}{a}"],
                        'rates': [rate1, rate2, rate3],
                        'profit_pct': profit_pct,
                        'net_profit_pct': net_profit,
                        'timestamp': datetime.now()
                    })
            
            # Verificar caminho reverso
            reverse_pairs = [f"{a}{c}", f"{c}{b}", f"{b}{a}"]
            if all(p in prices for p in reverse_pairs):
                start_amount = 1.0
                
                # Passo 1: A -> C
                rate1 = prices[f"{a}{c}"]
                amount1 = start_amount * rate1 * (1 - fee/100)
                
                # Passo 2: C -> B
                rate2 = prices[f"{c}{b}"]
                amount2 = amount1 * rate2 * (1 - fee/100)
                
                # Passo 3: B -> A
                rate3 = prices[f"{b}{a}"]
                final_amount = amount2 * rate3 * (1 - fee/100)
                
                profit_pct = (final_amount - start_amount) / start_amount * 100
                net_profit = profit_pct - (slippage * 3)
                
                if net_profit > min_profit:
                    opportunities.append({
                        'triangle': triangle,
                        'path': [f"{a}{c}", f"{c}{b}", f"{b}{a}"],
                        'rates': [rate1, rate2, rate3],
                        'profit_pct': profit_pct,
                        'net_profit_pct': net_profit,
                        'timestamp': datetime.now()
                    })
        
        # Ordenar por lucratividade
        opportunities.sort(key=lambda x: x['net_profit_pct'], reverse=True)
        return opportunities
    
    def generate_signal(self, symbol: str, current_price: float,
                       market_data: Optional[MarketData] = None,
                       historical_data: Optional[pd.DataFrame] = None,
                       positions: Optional[Dict[str, Any]] = None) -> Optional[Signal]:
        """
        Gera sinal de arbitragem
        Nota: Esta estratégia funciona melhor com múltiplos símbolos simultaneamente
        """
        # Para arbitragem, precisamos de preços de múltiplos pares
        # Esta implementação é simplificada para demonstração
        
        # Em uma implementação real, o engine precisaria fornecer
        # preços de todos os pares relevantes
        
        return None

class MLStrategy(Strategy):
    """
    Estratégia baseada em Machine Learning
    Usa modelos preditivos para gerar sinais
    """
    
    def _set_default_parameters(self) -> Dict[str, Any]:
        """Parâmetros específicos para ML Strategy"""
        params = super()._set_default_parameters()
        params.update({
            'model_type': 'random_forest',  # random_forest, gradient_boosting, neural_network
            'lookback_window': 50,
            'prediction_horizon': 5,
            'feature_columns': ['close', 'volume', 'rsi', 'macd', 'bb_width'],
            'confidence_threshold': 0.7,
            'retrain_interval': 100,  # número de novos candles
            'min_training_samples': 1000
        })
        return params
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calcula features para o modelo ML"""
        df = data.copy()
        
        # Features básicas
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift())
        df['volatility'] = df['returns'].rolling(window=20).std()
        
        # Features técnicas
        df['rsi'] = self._calculate_rsi(df['close'], 14)
        df['macd'], df['macd_signal'], df['macd_hist'] = self._calculate_macd(df['close'])
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # Volume features
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Price position
        df['price_position'] = (df['close'] - df['low'].rolling(window=20).min()) / \
                              (df['high'].rolling(window=20).max() - df['low'].rolling(window=20).min())
        
        # Lag features
        for lag in [1, 2, 3, 5, 10]:
            df[f'returns_lag_{lag}'] = df['returns'].shift(lag)
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
        
        # Target: Retorno futuro (binário: 1 se positivo, 0 se negativo)
        horizon = self.parameters['prediction_horizon']
        df['target'] = (df['close'].shift(-horizon) > df['close']).astype(int)
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcula RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calcula MACD"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    def train_model(self, data: pd.DataFrame):
        """Treina o modelo ML"""
        try:
            from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
            from sklearn.neural_network import MLPClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score, classification_report
            
            # Preparar dados
            df = data.copy()
            feature_cols = self.parameters['feature_columns']
            
            # Garantir que todas as features existem
            available_cols = [col for col in feature_cols if col in df.columns]
            
            if len(available_cols) < 3:
                logger.warning("Features insuficientes para treinamento ML")
                return False
            
            # Remover NaN
            df_clean = df[available_cols + ['target']].dropna()
            
            if len(df_clean) < self.parameters['min_training_samples']:
                logger.warning(f"Dados insuficientes para treinamento: {len(df_clean)} amostras")
                return False
            
            X = df_clean[available_cols].values
            y = df_clean['target'].values
            
            # Dividir treino/teste
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Normalizar
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Selecionar modelo
            model_type = self.parameters['model_type']
            
            if model_type == 'random_forest':
                model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
            elif model_type == 'gradient_boosting':
                model = GradientBoostingClassifier(
                    n_estimators=100,
                    max_depth=5,
                    random_state=42
                )
            elif model_type == 'neural_network':
                model = MLPClassifier(
                    hidden_layer_sizes=(50, 25),
                    max_iter=1000,
                    random_state=42
                )
            else:
                logger.error(f"Tipo de modelo desconhecido: {model_type}")
                return False
            
            # Treinar
            model.fit(X_train_scaled, y_train)
            
            # Avaliar
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            logger.info(f"Modelo ML treinado: {model_type}, Acurácia: {accuracy:.3f}")
            
            # Salvar modelo e scaler
            self.model = model
            self.scaler = scaler
            self.feature_cols = available_cols
            self.last_trained = datetime.now()
            self.model_accuracy = accuracy
            
            return True
            
        except ImportError:
            logger.error("Bibliotecas ML não instaladas. Instale scikit-learn.")
            return False
        except Exception as e:
            logger.error(f"Erro ao treinar modelo ML: {e}")
            return False
    
    def generate_signal(self, symbol: str, current_price: float,
                       market_data: Optional[MarketData] = None,
                       historical_data: Optional[pd.DataFrame] = None,
                       positions: Optional[Dict[str, Any]] = None) -> Optional[Signal]:
        """Gera sinal baseado em modelo ML"""
        if historical_data is None or len(historical_data) < 100:
            return None
        
        # Treinar modelo se necessário
        if not hasattr(self, 'model') or not self.model:
            df_features = self.calculate_indicators(historical_data)
            success = self.train_model(df_features)
            if not success:
                return None
        
        # Preparar features atuais
        df_current = historical_data.copy()
        df_features = self.calculate_indicators(df_current)
        
        # Obter última linha com todas as features
        if self.feature_cols:
            last_row = df_features[self.feature_cols].iloc[-1:].dropna()
            
            if len(last_row) > 0:
                # Normalizar
                X_scaled = self.scaler.transform(last_row.values)
                
                # Fazer predição
                try:
                    prediction = self.model.predict(X_scaled)[0]
                    proba = self.model.predict_proba(X_scaled)[0]
                    
                    # Determinar sinal baseado na predição
                    if prediction == 1 and proba[1] > self.parameters['confidence_threshold']:
                        signal_type = SignalType.BUY
                        strength = min(proba[1], 1.0)
                        confidence = proba[1]
                        rationale = f"ML prediz alta (conf: {proba[1]:.2f}, acc: {self.model_accuracy:.2f})"
                    
                    elif prediction == 0 and proba[0] > self.parameters['confidence_threshold']:
                        signal_type = SignalType.SELL
                        strength = -min(proba[0], 1.0)
                        confidence = proba[0]
                        rationale = f"ML prediz baixa (conf: {proba[0]:.2f}, acc: {self.model_accuracy:.2f})"
                    
                    else:
                        signal_type = SignalType.HOLD
                        strength = 0.0
                        confidence = max(proba)
                        rationale = f"ML inconclusivo (max conf: {max(proba):.2f})"
                    
                    # Criar sinal
                    signal = Signal(
                        type=signal_type,
                        strength=strength,
                        confidence=confidence,
                        price=current_price,
                        timestamp=datetime.now(),
                        symbol=symbol,
                        indicators={
                            'ml_prediction': int(prediction),
                            'ml_confidence': float(max(proba)),
                            'model_accuracy': self.model_accuracy,
                            'features_used': len(self.feature_cols)
                        },
                        rationale=rationale
                    )
                    
                    self.last_signal = signal
                    self.signals_generated += 1
                    
                    # Atualizar posição
                    if signal_type == SignalType.BUY:
                        self.position = 1
                    elif signal_type == SignalType.SELL:
                        self.position = -1
                    
                    return signal
                
                except Exception as e:
                    logger.error(f"Erro na predição ML: {e}")
        
        return None

class StrategyFactory:
    """
    Fábrica para criar instâncias de estratégias
    """
    
    @staticmethod
    def create_strategy(strategy_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[Strategy]:
        """
        Cria uma instância de estratégia pelo nome
        
        Args:
            strategy_name: Nome da estratégia
            config: Configuração da estratégia
            
        Returns:
            Instância da estratégia ou None se não encontrada
        """
        strategies = {
            'mean_reversion': MeanReversionStrategy,
            'trend_following': TrendFollowingStrategy,
            'arbitrage': ArbitrageStrategy,
            'ml_strategy': MLStrategy
        }
        
        strategy_class = strategies.get(strategy_name.lower())
        
        if strategy_class:
            return strategy_class(strategy_name, config)
        else:
            logger.error(f"Estratégia desconhecida: {strategy_name}")
            return None
    
    @staticmethod
    def get_available_strategies() -> List[Dict[str, Any]]:
        """Retorna lista de estratégias disponíveis"""
        return [
            {
                'name': 'mean_reversion',
                'display_name': 'Mean Reversion',
                'description': 'Estratégia de reversão à média usando Bollinger Bands e RSI',
                'parameters': {
                    'bb_period': {'type': 'int', 'default': 20, 'min': 10, 'max': 50},
                    'bb_std': {'type': 'float', 'default': 2.0, 'min': 1.0, 'max': 3.0},
                    'rsi_period': {'type': 'int', 'default': 14, 'min': 7, 'max': 21}
                }
            },
            {
                'name': 'trend_following',
                'display_name': 'Trend Following',
                'description': 'Estratégia de seguimento de tendência usando Médias Móveis e MACD',
                'parameters': {
                    'fast_ma': {'type': 'int', 'default': 9, 'min': 5, 'max': 20},
                    'slow_ma': {'type': 'int', 'default': 21, 'min': 15, 'max': 50},
                    'adx_threshold': {'type': 'float', 'default': 25, 'min': 15, 'max': 40}
                }
            },
            {
                'name': 'ml_strategy',
                'display_name': 'Machine Learning',
                'description': 'Estratégia baseada em modelos preditivos de ML',
                'parameters': {
                    'model_type': {'type': 'select', 'options': ['random_forest', 'gradient_boosting'], 'default': 'random_forest'},
                    'confidence_threshold': {'type': 'float', 'default': 0.7, 'min': 0.5, 'max': 0.95}
                }
            }
        ]