import threading
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime

from .binance_client import BinanceClient
from .strategies.base_strategy import BaseStrategy
from .strategies.sma_crossover import SMACrossoverStrategy
from .strategies.rsi_strategy import RSIStrategy

class TradingEngine:
    """Motor principal de trading com suporte a múltiplos pares"""
    
    def __init__(self, binance_client: BinanceClient):
        self.binance_client = binance_client
        self.logger = logging.getLogger(__name__)
        
        # Estratégias disponíveis
        self.strategies = {
            'sma': SMACrossoverStrategy(),
            'rsi': RSIStrategy()
        }
        
        # Estado do trading
        self.is_trading = False
        self.current_strategy = None
        self.active_trades = {}  # Agora suporta múltiplos trades
        self.trade_history = []
        
        # Configurações de trading por par
        self.trading_pairs = {}  # symbol -> {strategy, quantity, last_signal}
        
        # Thread de execução
        self.trading_thread = None
        
    def start_auto_trading(self, strategy_name: str, symbol: str, quantity: float) -> bool:
        """Inicia trading automático para um par específico"""
        if strategy_name not in self.strategies:
            self.logger.error(f"Estratégia {strategy_name} não encontrada")
            return False
            
        # Adiciona o par à lista de trades ativos
        self.trading_pairs[symbol] = {
            'strategy': self.strategies[strategy_name],
            'quantity': quantity,
            'last_signal': None,
            'is_opened': False
        }
        
        # Se não está trading, inicia o loop
        if not self.is_trading:
            self.is_trading = True
            self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
            self.trading_thread.start()
            self.logger.info(f"Loop de trading iniciado com {len(self.trading_pairs)} pares")
        
        self.logger.info(f"Trading automático iniciado: {strategy_name} - {symbol} - Qtd: {quantity}")
        return True
    
    def stop_auto_trading(self, symbol: str = None):
        """Para o trading automático para um par específico ou todos"""
        if symbol:
            if symbol in self.trading_pairs:
                del self.trading_pairs[symbol]
                self.logger.info(f"Trading parado para {symbol}")
            
            # Se não há mais pares, para o loop
            if not self.trading_pairs:
                self.is_trading = False
                self.logger.info("Todos os pares de trading parados")
        else:
            # Para tudo
            self.trading_pairs.clear()
            self.is_trading = False
            self.logger.info("Trading automático completamente parado")
    
    def _trading_loop(self):
        """Loop principal de trading para múltiplos pares"""
        while self.is_trading and self.trading_pairs:
            try:
                # Processa cada par de trading
                for symbol, trade_info in list(self.trading_pairs.items()):
                    self._process_trading_pair(symbol, trade_info)
                
                time.sleep(60)  # Espera 1 minuto entre verificações
                
            except Exception as e:
                self.logger.error(f"Erro no loop de trading: {e}")
                time.sleep(30)
    
    def _process_trading_pair(self, symbol: str, trade_info: Dict):
        """Processa decisões de trading para um par específico"""
        try:
            # Obtém dados de mercado
            klines = self.binance_client.get_klines(symbol, '1m', 100)
            if not klines:
                return
            
            # Extrai preços de fechamento
            prices = [float(candle[4]) for candle in klines]
            current_price = prices[-1]
            
            # Prepara dados para estratégia
            data = {
                'prices': prices,
                'current_price': current_price,
                'symbol': symbol
            }
            
            strategy = trade_info['strategy']
            quantity = trade_info['quantity']
            is_opened = trade_info['is_opened']
            
            # Executa estratégia
            if strategy.should_buy(data) and not is_opened:
                self._execute_trade(symbol, "BUY", quantity, strategy.name)
                trade_info['is_opened'] = True
                trade_info['last_signal'] = 'BUY'
                
            elif strategy.should_sell(data) and is_opened:
                self._execute_trade(symbol, "SELL", quantity, strategy.name)
                trade_info['is_opened'] = False
                trade_info['last_signal'] = 'SELL'
                
        except Exception as e:
            self.logger.error(f"Erro ao processar par {symbol}: {e}")
    
    def _execute_trade(self, symbol: str, side: str, quantity: float, strategy_name: str):
        """Executa uma ordem de trading"""
        try:
            # Verifica se temos saldo suficiente
            base_asset = symbol.replace('USDT', '')
            quote_asset = 'USDT'
            
            if side == "BUY":
                # Para comprar, precisamos de USDT
                account_info = self.binance_client.get_account_info()
                if account_info:
                    usdt_balance = 0
                    for balance in account_info['balances']:
                        if balance['asset'] == quote_asset:
                            usdt_balance = float(balance['free'])
                            break
                    
                    # Calcula custo aproximado
                    current_price = self.binance_client.get_ticker_price(symbol)
                    if current_price and usdt_balance < (current_price * quantity):
                        self.logger.warning(f"Saldo de {quote_asset} insuficiente para comprar {symbol}")
                        return
            
            result = self.binance_client.create_order(symbol, side, quantity)
            
            if result:
                # Atualiza status da posição
                if side == "BUY":
                    self.active_trades[symbol] = {
                        'side': 'BUY',
                        'quantity': quantity,
                        'entry_price': float(result['fills'][0]['price']) if result.get('fills') else 0,
                        'timestamp': datetime.now(),
                        'strategy': strategy_name
                    }
                else:
                    if symbol in self.active_trades:
                        del self.active_trades[symbol]
                
                # Registra no histórico
                trade_info = {
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': float(result['fills'][0]['price']) if result.get('fills') else 0,
                    'timestamp': datetime.now(),
                    'strategy': strategy_name
                }
                
                self.trade_history.append(trade_info)
                self.logger.info(f"{side} executado: {quantity} {symbol}")
                
        except Exception as e:
            self.logger.error(f"Erro na ordem {side} para {symbol}: {e}")
    
    def manual_trade(self, symbol: str, side: str, quantity: float) -> bool:
        """Executa trade manual"""
        try:
            result = self.binance_client.create_order(symbol, side, quantity)
            
            if result:
                # Atualiza histórico
                trade_info = {
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': float(result['fills'][0]['price']) if result.get('fills') else 0,
                    'timestamp': datetime.now(),
                    'strategy': 'Manual'
                }
                
                self.trade_history.append(trade_info)
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Erro no trade manual: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Retorna status atual do trading"""
        status_info = {
            'trading_ativo': self.is_trading,
            'pares_ativos': list(self.trading_pairs.keys()),
            'trades_ativos': len(self.active_trades),
            'total_historico_trades': len(self.trade_history),
            'pares_detalhes': {}
        }
        
        # Adiciona detalhes de cada par
        for symbol, trade_info in self.trading_pairs.items():
            current_price = self.binance_client.get_ticker_price(symbol)
            status_info['pares_detalhes'][symbol] = {
                'estrategia': trade_info['strategy'].name,
                'quantidade': trade_info['quantity'],
                'posicao_aberta': trade_info['is_opened'],
                'ultimo_sinal': trade_info['last_signal'],
                'preco_atual': current_price
            }
        
        return status_info
    
    def get_account_balances(self) -> Dict:
        """Retorna saldos da conta"""
        try:
            account_info = self.binance_client.get_account_info()
            if not account_info:
                return {}
            
            balances = {}
            for balance in account_info['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                if free > 0 or locked > 0:
                    balances[asset] = {
                        'free': free,
                        'locked': locked,
                        'total': free + locked
                    }
            
            return balances
            
        except Exception as e:
            self.logger.error(f"Erro ao obter saldos: {e}")
            return {}