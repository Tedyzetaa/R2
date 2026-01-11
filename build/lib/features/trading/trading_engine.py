"""
Trading Engine - Motor de execução de trading quantitativo
Sistema central para análise, decisão e execução de trades
"""

import asyncio
import logging
import threading
import time
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import pandas as pd
import numpy as np
from decimal import Decimal, ROUND_DOWN

from .binance_client import BinanceClient, MarketData, Order, OrderSide, OrderStatus, Kline
from .strategies import Strategy, Signal
from .risk_manager import RiskManager, RiskAssessment

logger = logging.getLogger(__name__)

class TradingMode(Enum):
    """Modos de operação do trading engine"""
    PAPER = "paper"  # Simulação sem execução real
    LIVE = "live"    # Execução real com API
    BACKTEST = "backtest"  # Teste histórico

class OrderExecutionMode(Enum):
    """Modos de execução de ordens"""
    AGGRESSIVE = "aggressive"  # Preço de mercado
    PASSIVE = "passive"       # Ordem limite
    HYBRID = "hybrid"         # Mistura de ambos

@dataclass
class Position:
    """Posição aberta no mercado"""
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    current_price: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    unrealized_pnl: float = 0.0
    unrealized_pnl_percent: float = 0.0
    realized_pnl: float = 0.0
    commission_paid: float = 0.0
    
    def update_price(self, current_price: float):
        """Atualiza preço atual e calcula P&L"""
        self.current_price = current_price
        
        if self.side == OrderSide.BUY:
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
        else:  # SELL (short)
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity
        
        if self.entry_price > 0:
            self.unrealized_pnl_percent = (self.unrealized_pnl / (self.entry_price * self.quantity)) * 100
    
    def should_stop_loss(self) -> bool:
        """Verifica se stop loss foi atingido"""
        if not self.stop_loss:
            return False
        
        if self.side == OrderSide.BUY:
            return self.current_price <= self.stop_loss
        else:  # SELL
            return self.current_price >= self.stop_loss
    
    def should_take_profit(self) -> bool:
        """Verifica se take profit foi atingido"""
        if not self.take_profit:
            return False
        
        if self.side == OrderSide.BUY:
            return self.current_price >= self.take_profit
        else:  # SELL
            return self.current_price <= self.take_profit
    
    def update_trailing_stop(self, current_price: float):
        """Atualiza stop loss trailing"""
        if not self.trailing_stop:
            return
        
        if self.side == OrderSide.BUY:
            new_stop = current_price * (1 - self.trailing_stop)
            if new_stop > (self.stop_loss or 0):
                self.stop_loss = new_stop
        else:  # SELL
            new_stop = current_price * (1 + self.trailing_stop)
            if new_stop < (self.stop_loss or float('inf')):
                self.stop_loss = new_stop

@dataclass
class Trade:
    """Trade completo (entrada e saída)"""
    trade_id: str
    symbol: str
    side: OrderSide
    entry_order: Order
    exit_order: Optional[Order] = None
    entry_time: datetime = field(default_factory=datetime.now)
    exit_time: Optional[datetime] = None
    quantity: float = 0.0
    entry_price: float = 0.0
    exit_price: Optional[float] = None
    pnl: float = 0.0
    pnl_percent: float = 0.0
    commission: float = 0.0
    fees: float = 0.0
    reason: str = ""
    
    @property
    def duration(self) -> Optional[float]:
        """Duração do trade em segundos"""
        if self.exit_time:
            return (self.exit_time - self.entry_time).total_seconds()
        return None
    
    @property
    def is_closed(self) -> bool:
        """Se o trade está fechado"""
        return self.exit_order is not None and self.exit_order.is_filled
    
    def calculate_pnl(self):
        """Calcula P&L do trade"""
        if self.exit_price and self.entry_price > 0:
            if self.side == OrderSide.BUY:
                self.pnl = (self.exit_price - self.entry_price) * self.quantity
            else:  # SELL
                self.pnl = (self.entry_price - self.exit_price) * self.quantity
            
            self.pnl_percent = (self.pnl / (self.entry_price * self.quantity)) * 100
            
            # Subtrair comissões
            self.pnl -= self.commission + self.fees

@dataclass
class PerformanceMetrics:
    """Métricas de performance do trading"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    total_commission: float = 0.0
    total_fees: float = 0.0
    net_profit: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    average_trade_duration: float = 0.0
    volatility: float = 0.0
    calmar_ratio: float = 0.0
    sortino_ratio: float = 0.0
    
    def update_from_trades(self, trades: List[Trade]):
        """Atualiza métricas a partir de lista de trades"""
        if not trades:
            return
        
        closed_trades = [t for t in trades if t.is_closed]
        if not closed_trades:
            return
        
        self.total_trades = len(closed_trades)
        self.winning_trades = len([t for t in closed_trades if t.pnl > 0])
        self.losing_trades = len([t for t in closed_trades if t.pnl < 0])
        
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades * 100
        
        # P&L total
        self.total_pnl = sum(t.pnl for t in closed_trades)
        self.total_commission = sum(t.commission for t in closed_trades)
        self.total_fees = sum(t.fees for t in closed_trades)
        self.net_profit = self.total_pnl - self.total_commission - self.total_fees
        
        # Wins e losses
        wins = [t.pnl for t in closed_trades if t.pnl > 0]
        losses = [t.pnl for t in closed_trades if t.pnl < 0]
        
        if wins:
            self.largest_win = max(wins)
            self.average_win = sum(wins) / len(wins)
        
        if losses:
            self.largest_loss = min(losses)
            self.average_loss = sum(losses) / len(losses)
        
        # Profit factor
        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 0
        if total_losses > 0:
            self.profit_factor = total_wins / total_losses
        
        # Duração média
        durations = [t.duration for t in closed_trades if t.duration]
        if durations:
            self.average_trade_duration = sum(durations) / len(durations)
        
        # Calcular drawdown
        self._calculate_drawdown(closed_trades)
        
        # Calcular ratios
        self._calculate_ratios(closed_trades)
    
    def _calculate_drawdown(self, trades: List[Trade]):
        """Calcula drawdown máximo"""
        if not trades:
            return
        
        # Ordenar por tempo
        sorted_trades = sorted(trades, key=lambda t: t.entry_time)
        
        cumulative_pnl = 0
        peak = 0
        max_dd = 0
        max_dd_percent = 0
        
        equity_curve = []
        
        for trade in sorted_trades:
            if trade.is_closed:
                cumulative_pnl += trade.pnl
                equity_curve.append(cumulative_pnl)
                
                if cumulative_pnl > peak:
                    peak = cumulative_pnl
                
                drawdown = peak - cumulative_pnl
                drawdown_percent = (drawdown / peak * 100) if peak > 0 else 0
                
                if drawdown > max_dd:
                    max_dd = drawdown
                    max_dd_percent = drawdown_percent
        
        self.max_drawdown = max_dd
        self.max_drawdown_percent = max_dd_percent
    
    def _calculate_ratios(self, trades: List[Trade]):
        """Calcula ratios de performance"""
        if not trades:
            return
        
        # Retornos diários (simplificado)
        returns = [t.pnl_percent / 100 for t in trades if t.is_closed]
        
        if len(returns) < 2:
            return
        
        returns_array = np.array(returns)
        
        # Sharpe Ratio (assumindo risk-free rate = 0)
        if returns_array.std() > 0:
            self.sharpe_ratio = returns_array.mean() / returns_array.std() * np.sqrt(252)
        
        # Sortino Ratio (usando apenas retornos negativos)
        negative_returns = returns_array[returns_array < 0]
        if len(negative_returns) > 0 and negative_returns.std() > 0:
            self.sortino_ratio = returns_array.mean() / negative_returns.std() * np.sqrt(252)
        
        # Calmar Ratio
        if self.max_drawdown_percent > 0:
            annual_return = returns_array.mean() * 252
            self.calmar_ratio = annual_return / self.max_drawdown_percent
        
        # Volatilidade
        self.volatility = returns_array.std() * np.sqrt(252)

@dataclass
class TradingSession:
    """Sessão de trading com configurações específicas"""
    session_id: str
    symbol: str
    strategy: Strategy
    initial_capital: float
    mode: TradingMode
    start_time: datetime
    end_time: Optional[datetime] = None
    positions: Dict[str, Position] = field(default_factory=dict)
    trades: List[Trade] = field(default_factory=list)
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    is_active: bool = True
    
    def add_trade(self, trade: Trade):
        """Adiciona trade à sessão"""
        self.trades.append(trade)
        self.performance.update_from_trades(self.trades)
    
    def close_position(self, symbol: str, exit_order: Order):
        """Fecha uma posição aberta"""
        if symbol in self.positions:
            position = self.positions[symbol]
            
            # Criar trade
            trade = Trade(
                trade_id=f"TRADE-{int(time.time())}-{len(self.trades)}",
                symbol=symbol,
                side=position.side,
                entry_order=Order(  # Ordem fictícia para posição
                    order_id=f"POS-{symbol}",
                    client_order_id=f"pos_{symbol}",
                    symbol=symbol,
                    side=position.side,
                    type=OrderType.MARKET,
                    quantity=position.quantity,
                    price=position.entry_price,
                    status=OrderStatus.FILLED,
                    executed_qty=position.quantity,
                    cummulative_quote_qty=position.entry_price * position.quantity,
                    created_at=position.entry_time
                ),
                exit_order=exit_order,
                entry_time=position.entry_time,
                exit_time=datetime.now(),
                quantity=position.quantity,
                entry_price=position.entry_price,
                exit_price=exit_order.average_price,
                commission=position.commission_paid,
                reason="Position closed"
            )
            
            trade.calculate_pnl()
            self.add_trade(trade)
            
            # Remover posição
            del self.positions[symbol]
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Retorna resumo da sessão"""
        return {
            'session_id': self.session_id,
            'symbol': self.symbol,
            'mode': self.mode.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_active': self.is_active,
            'open_positions': len(self.positions),
            'total_trades': len(self.trades),
            'closed_trades': len([t for t in self.trades if t.is_closed]),
            'performance': {
                'net_profit': self.performance.net_profit,
                'win_rate': self.performance.win_rate,
                'profit_factor': self.performance.profit_factor,
                'max_drawdown': self.performance.max_drawdown_percent
            }
        }

class TradingEngine:
    """
    Motor principal de trading quantitativo
    Gerencia estratégias, execução e risco
    """
    
    def __init__(self, binance_client: BinanceClient, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o trading engine
        
        Args:
            binance_client: Cliente Binance configurado
            config: Configuração do engine
        """
        self.client = binance_client
        self.config = config or {}
        
        # Sessões de trading ativas
        self.sessions: Dict[str, TradingSession] = {}
        
        # Estratégias
        self.strategies: Dict[str, Strategy] = {}
        
        # Gerenciamento de risco
        self.risk_manager = RiskManager(config.get('risk', {}))
        
        # Dados de mercado
        self.market_data: Dict[str, MarketData] = {}
        self.klines: Dict[str, List[Kline]] = {}
        
        # Estado do engine
        self.is_running = False
        self.engine_thread: Optional[threading.Thread] = None
        self.update_interval = self.config.get('update_interval', 1.0)  # segundos
        
        # Callbacks
        self.callbacks: Dict[str, List[Callable]] = {
            'on_signal': [],
            'on_order': [],
            'on_trade': [],
            'on_error': []
        }
        
        # Estatísticas
        self.stats = {
            'signals_generated': 0,
            'orders_executed': 0,
            'trades_completed': 0,
            'errors': 0,
            'last_update': None
        }
        
        logger.info("Trading Engine inicializado")
    
    def register_callback(self, event: str, callback: Callable):
        """Registra callback para evento"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
            logger.debug(f"Callback registrado para evento: {event}")
    
    def _notify_callbacks(self, event: str, data: Any):
        """Notifica todos os callbacks de um evento"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Erro no callback {event}: {e}")
    
    def start(self):
        """Inicia o trading engine"""
        if self.is_running:
            logger.warning("Trading Engine já está rodando")
            return
        
        self.is_running = True
        self.engine_thread = threading.Thread(target=self._run_engine, daemon=True)
        self.engine_thread.start()
        
        logger.info("Trading Engine iniciado")
    
    def stop(self):
        """Para o trading engine"""
        self.is_running = False
        if self.engine_thread:
            self.engine_thread.join(timeout=10)
        
        # Fechar todas as sessões
        for session_id, session in list(self.sessions.items()):
            self.close_session(session_id)
        
        logger.info("Trading Engine parado")
    
    def _run_engine(self):
        """Loop principal do engine (executado em thread separada)"""
        import time
        
        while self.is_running:
            try:
                start_time = time.time()
                
                # Atualizar dados de mercado
                self._update_market_data()
                
                # Processar estratégias
                self._process_strategies()
                
                # Gerenciar posições abertas
                self._manage_positions()
                
                # Atualizar estatísticas
                self.stats['last_update'] = datetime.now()
                
                # Calcular tempo de processamento
                processing_time = time.time() - start_time
                
                # Aguardar próximo ciclo
                sleep_time = max(0, self.update_interval - processing_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f"Erro no loop do Trading Engine: {e}")
                self.stats['errors'] += 1
                self._notify_callbacks('on_error', {'error': str(e), 'timestamp': datetime.now()})
                time.sleep(5)  # Pausa em caso de erro
    
    async def _update_market_data_async(self):
        """Atualiza dados de mercado de forma assíncrona"""
        # Atualizar tickers para símbolos ativos
        active_symbols = set(session.symbol for session in self.sessions.values())
        
        for symbol in active_symbols:
            try:
                ticker = await self.client.get_ticker(symbol)
                if ticker:
                    self.market_data[symbol] = ticker
                    
                    # Atualizar preços nas posições
                    for session in self.sessions.values():
                        if symbol in session.positions:
                            position = session.positions[symbol]
                            position.update_price(ticker.last_price)
                            
                            # Atualizar trailing stop
                            position.update_trailing_stop(ticker.last_price)
            
            except Exception as e:
                logger.error(f"Erro ao atualizar market data para {symbol}: {e}")
    
    def _update_market_data(self):
        """Atualiza dados de mercado (chamado da thread principal)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._update_market_data_async())
            loop.close()
        except Exception as e:
            logger.error(f"Erro na atualização de market data: {e}")
    
    def _process_strategies(self):
        """Processa todas as estratégias ativas"""
        for session_id, session in self.sessions.items():
            if not session.is_active:
                continue
            
            try:
                # Obter dados para a estratégia
                symbol = session.symbol
                
                if symbol not in self.market_data:
                    continue
                
                current_price = self.market_data[symbol].last_price
                
                # Gerar sinal da estratégia
                signal = session.strategy.generate_signal(
                    symbol=symbol,
                    current_price=current_price,
                    market_data=self.market_data.get(symbol),
                    positions=session.positions
                )
                
                if signal and signal.strength != 0:
                    self.stats['signals_generated'] += 1
                    
                    # Avaliar risco
                    risk_assessment = self.risk_manager.assess_trade(
                        symbol=symbol,
                        signal=signal,
                        current_price=current_price,
                        positions=session.positions,
                        capital=session.initial_capital
                    )
                    
                    if risk_assessment.is_approved:
                        # Executar trade baseado no sinal
                        self._execute_signal(session, signal, risk_assessment)
                    
                    # Notificar callbacks
                    self._notify_callbacks('on_signal', {
                        'session_id': session_id,
                        'symbol': symbol,
                        'signal': signal.to_dict(),
                        'risk_assessment': risk_assessment.to_dict(),
                        'timestamp': datetime.now()
                    })
            
            except Exception as e:
                logger.error(f"Erro ao processar estratégia para sessão {session_id}: {e}")
    
    def _execute_signal(self, session: TradingSession, signal: Signal, 
                       risk_assessment: RiskAssessment):
        """Executa um sinal de trading"""
        try:
            symbol = session.symbol
            current_price = self.market_data[symbol].last_price if symbol in self.market_data else 0
            
            # Determinar side baseado no sinal
            if signal.strength > 0:
                side = OrderSide.BUY
            else:
                side = OrderSide.SELL
            
            # Calcular quantidade baseada no gerenciamento de risco
            quantity = risk_assessment.recommended_quantity
            
            # Verificar se já existe posição aberta
            if symbol in session.positions:
                position = session.positions[symbol]
                
                # Se o sinal é oposto à posição atual, considerar fechamento
                if (position.side == OrderSide.BUY and side == OrderSide.SELL) or \
                   (position.side == OrderSide.SELL and side == OrderSide.BUY):
                    
                    # Fechar posição existente
                    self._close_position(session, symbol, "Reverse signal")
                    
                    # Abrir nova posição (se aprovado)
                    if risk_assessment.is_approved:
                        self._open_position(session, side, quantity, current_price, 
                                          risk_assessment, signal)
            
            else:
                # Abrir nova posição
                if risk_assessment.is_approved:
                    self._open_position(session, side, quantity, current_price, 
                                      risk_assessment, signal)
        
        except Exception as e:
            logger.error(f"Erro ao executar sinal: {e}")
            self._notify_callbacks('on_error', {
                'error': f"Erro na execução do sinal: {e}",
                'session_id': session.session_id,
                'timestamp': datetime.now()
            })
    
    async def _open_position_async(self, session: TradingSession, side: OrderSide, 
                                  quantity: float, price: float,
                                  risk_assessment: RiskAssessment, signal: Signal) -> Optional[Position]:
        """Abre uma posição (assíncrona)"""
        try:
            symbol = session.symbol
            
            # Criar ordem
            order_type = self.config.get('order_type', 'MARKET')
            
            order = await self.client.create_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price if order_type != 'MARKET' else None
            )
            
            if order and order.is_filled:
                self.stats['orders_executed'] += 1
                
                # Criar posição
                position = Position(
                    symbol=symbol,
                    side=side,
                    quantity=order.executed_qty,
                    entry_price=order.average_price,
                    current_price=order.average_price,
                    entry_time=order.created_at,
                    stop_loss=risk_assessment.stop_loss_price,
                    take_profit=risk_assessment.take_profit_price,
                    trailing_stop=risk_assessment.trailing_stop_percent,
                    commission_paid=order.cummulative_quote_qty * 0.001  # Estimativa
                )
                
                session.positions[symbol] = position
                
                # Notificar callbacks
                self._notify_callbacks('on_order', {
                    'session_id': session.session_id,
                    'order': order,
                    'position': position,
                    'timestamp': datetime.now()
                })
                
                logger.info(f"Posição aberta: {symbol} {side.value} {quantity} @ {order.average_price}")
                return position
        
        except Exception as e:
            logger.error(f"Erro ao abrir posição: {e}")
        
        return None
    
    def _open_position(self, session: TradingSession, side: OrderSide, 
                      quantity: float, price: float,
                      risk_assessment: RiskAssessment, signal: Signal):
        """Abre uma posição (wrapper síncrono)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            position = loop.run_until_complete(
                self._open_position_async(session, side, quantity, price, risk_assessment, signal)
            )
            
            loop.close()
            
            return position
        
        except Exception as e:
            logger.error(f"Erro na abertura de posição: {e}")
            return None
    
    async def _close_position_async(self, session: TradingSession, symbol: str, 
                                   reason: str = "") -> Optional[Order]:
        """Fecha uma posição (assíncrona)"""
        try:
            if symbol not in session.positions:
                return None
            
            position = session.positions[symbol]
            
            # Determinar side oposto para fechamento
            close_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY
            
            # Criar ordem de fechamento
            order = await self.client.create_order(
                symbol=symbol,
                side=close_side,
                order_type='MARKET',  # Fechamento sempre a mercado
                quantity=position.quantity
            )
            
            if order and order.is_filled:
                session.close_position(symbol, order)
                self.stats['trades_completed'] += 1
                
                # Notificar callbacks
                self._notify_callbacks('on_trade', {
                    'session_id': session.session_id,
                    'position': position,
                    'exit_order': order,
                    'reason': reason,
                    'timestamp': datetime.now()
                })
                
                logger.info(f"Posição fechada: {symbol} {close_side.value} {position.quantity} @ {order.average_price}")
                return order
        
        except Exception as e:
            logger.error(f"Erro ao fechar posição: {e}")
        
        return None
    
    def _close_position(self, session: TradingSession, symbol: str, reason: str = ""):
        """Fecha uma posição (wrapper síncrono)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            order = loop.run_until_complete(
                self._close_position_async(session, symbol, reason)
            )
            
            loop.close()
            
            return order
        
        except Exception as e:
            logger.error(f"Erro no fechamento de posição: {e}")
            return None
    
    def _manage_positions(self):
        """Gerencia posições abertas (stop loss, take profit)"""
        for session_id, session in self.sessions.items():
            if not session.is_active:
                continue
            
            for symbol, position in list(session.positions.items()):
                try:
                    # Verificar stop loss
                    if position.should_stop_loss():
                        logger.info(f"Stop loss atingido para {symbol}")
                        self._close_position(session, symbol, "Stop loss")
                        continue
                    
                    # Verificar take profit
                    if position.should_take_profit():
                        logger.info(f"Take profit atingido para {symbol}")
                        self._close_position(session, symbol, "Take profit")
                        continue
                    
                    # Verificar timeout (posição aberta por muito tempo)
                    position_age = (datetime.now() - position.entry_time).total_seconds()
                    max_position_age = self.config.get('max_position_age_hours', 24) * 3600
                    
                    if position_age > max_position_age:
                        logger.info(f"Posição expirada por timeout: {symbol}")
                        self._close_position(session, symbol, "Position timeout")
                
                except Exception as e:
                    logger.error(f"Erro ao gerenciar posição {symbol}: {e}")
    
    def create_session(self, symbol: str, strategy: Strategy, 
                      initial_capital: float, mode: TradingMode = TradingMode.PAPER) -> str:
        """
        Cria uma nova sessão de trading
        
        Args:
            symbol: Símbolo do par
            strategy: Estratégia a ser usada
            initial_capital: Capital inicial
            mode: Modo de trading
            
        Returns:
            ID da sessão criada
        """
        session_id = f"SESS-{int(time.time())}-{len(self.sessions)}"
        
        session = TradingSession(
            session_id=session_id,
            symbol=symbol,
            strategy=strategy,
            initial_capital=initial_capital,
            mode=mode,
            start_time=datetime.now()
        )
        
        self.sessions[session_id] = session
        self.strategies[session_id] = strategy
        
        logger.info(f"Sessão criada: {session_id} ({symbol}, {mode.value})")
        return session_id
    
    def close_session(self, session_id: str):
        """Fecha uma sessão de trading"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.is_active = False
            session.end_time = datetime.now()
            
            # Fechar todas as posições abertas
            for symbol in list(session.positions.keys()):
                self._close_position(session, symbol, "Session closed")
            
            logger.info(f"Sessão fechada: {session_id}")
            
            return session.get_session_summary()
        
        return None
    
    def get_session(self, session_id: str) -> Optional[TradingSession]:
        """Obtém uma sessão pelo ID"""
        return self.sessions.get(session_id)
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Obtém resumo de todas as sessões"""
        return [sess.get_session_summary() for sess in self.sessions.values()]
    
    def get_engine_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do engine"""
        return {
            **self.stats,
            'active_sessions': len([s for s in self.sessions.values() if s.is_active]),
            'total_sessions': len(self.sessions),
            'market_data_symbols': len(self.market_data),
            'update_interval': self.update_interval,
            'is_running': self.is_running,
            'risk_manager_status': self.risk_manager.get_status()
        }
    
    async def backtest(self, symbol: str, strategy: Strategy,
                      start_date: str, end_date: str,
                      initial_capital: float = 10000.0,
                      interval: str = '1h') -> Dict[str, Any]:
        """
        Executa backtest de uma estratégia
        
        Args:
            symbol: Símbolo do par
            strategy: Estratégia para testar
            start_date: Data de início
            end_date: Data de fim
            initial_capital: Capital inicial
            interval: Intervalo dos dados
            
        Returns:
            Resultados do backtest
        """
        logger.info(f"Iniciando backtest: {symbol} ({start_date} to {end_date})")
        
        # Obter dados históricos
        klines = await self.client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=start_date,
            end_str=end_date
        )
        
        if not klines:
            return {'error': 'No historical data available'}
        
        # Converter para DataFrame
        df = pd.DataFrame([{
            'timestamp': k.open_time,
            'open': k.open_price,
            'high': k.high_price,
            'low': k.low_price,
            'close': k.close_price,
            'volume': k.volume
        } for k in klines])
        
        df.set_index('timestamp', inplace=True)
        
        # Simular trading
        capital = initial_capital
        position = 0
        trades = []
        equity_curve = [capital]
        
        strategy.initialize(df)
        
        for i in range(1, len(df)):
            current_data = df.iloc[:i]
            current_price = df.iloc[i]['close']
            
            # Gerar sinal
            signal = strategy.generate_signal(
                symbol=symbol,
                current_price=current_price,
                historical_data=current_data
            )
            
            if signal and signal.strength != 0:
                # Simular execução
                if signal.strength > 0 and position == 0:  # BUY
                    position = capital / current_price
                    capital = 0
                    trades.append({
                        'type': 'BUY',
                        'price': current_price,
                        'timestamp': df.index[i],
                        'quantity': position
                    })
                
                elif signal.strength < 0 and position > 0:  # SELL
                    capital = position * current_price
                    position = 0
                    trades.append({
                        'type': 'SELL',
                        'price': current_price,
                        'timestamp': df.index[i],
                        'quantity': position
                    })
            
            # Calcular equity
            current_equity = capital + (position * current_price if position > 0 else 0)
            equity_curve.append(current_equity)
        
        # Fechar posição aberta no final
        if position > 0:
            last_price = df.iloc[-1]['close']
            capital = position * last_price
            trades.append({
                'type': 'SELL',
                'price': last_price,
                'timestamp': df.index[-1],
                'quantity': position
            })
        
        # Calcular métricas
        final_capital = capital
        total_return = (final_capital - initial_capital) / initial_capital * 100
        
        # Calcular drawdown
        equity_series = pd.Series(equity_curve)
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        # Calcular Sharpe ratio (simplificado)
        returns = equity_series.pct_change().dropna()
        if returns.std() > 0:
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe = 0
        
        results = {
            'symbol': symbol,
            'strategy': strategy.name,
            'period': f"{start_date} to {end_date}",
            'initial_capital': initial_capital,
            'final_capital': final_capital,
            'total_return_percent': total_return,
            'total_trades': len(trades),
            'max_drawdown_percent': max_drawdown,
            'sharpe_ratio': sharpe,
            'win_rate': 0,  # Seria calculado com mais detalhes
            'profit_factor': 0,
            'trades': trades[:100],  # Limitar número de trades retornados
            'equity_curve': equity_curve
        }
        
        logger.info(f"Backtest concluído: {total_return:.2f}% retorno, {len(trades)} trades")
        return results