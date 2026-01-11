"""
Binance Client - Cliente profissional para API da Binance
Integração completa com REST API e WebSocket para dados em tempo real
"""

import hmac
import hashlib
import json
import logging
import time
import asyncio
import websockets
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from decimal import Decimal
import uuid

import aiohttp
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class OrderType(Enum):
    """Tipos de ordem suportados pela Binance"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
    LIMIT_MAKER = "LIMIT_MAKER"

class OrderSide(Enum):
    """Lados da ordem"""
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    """Status das ordens"""
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    PENDING_CANCEL = "PENDING_CANCEL"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class TimeInForce(Enum):
    """Tempo de vigência da ordem"""
    GTC = "GTC"  # Good Till Canceled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill

@dataclass
class MarketData:
    """Dados de mercado consolidados"""
    symbol: str
    timestamp: datetime
    bid_price: float
    ask_price: float
    last_price: float
    volume_24h: float
    high_24h: float
    low_24h: float
    price_change_24h: float
    price_change_percent_24h: float
    weighted_avg_price: float
    open_price: float
    close_price: float
    quote_volume: float
    bid_qty: float
    ask_qty: float
    trades_24h: int
    
    @property
    def spread(self) -> float:
        """Spread entre bid e ask"""
        return self.ask_price - self.bid_price
    
    @property
    def spread_percent(self) -> float:
        """Spread percentual"""
        if self.bid_price > 0:
            return (self.spread / self.bid_price) * 100
        return 0.0

@dataclass
class OrderBook:
    """Livro de ordens"""
    symbol: str
    timestamp: datetime
    bids: List[Tuple[float, float]]  # (price, quantity)
    asks: List[Tuple[float, float]]
    
    @property
    def bid_depth(self) -> float:
        """Profundidade total do lado de compra"""
        return sum(qty for _, qty in self.bids[:10])  # Top 10 níveis
    
    @property
    def ask_depth(self) -> float:
        """Profundidade total do lado de venda"""
        return sum(qty for _, qty in self.asks[:10])  # Top 10 níveis
    
    @property
    def imbalance(self) -> float:
        """Desequilíbrio entre oferta e demanda"""
        total = self.bid_depth + self.ask_depth
        if total > 0:
            return (self.bid_depth - self.ask_depth) / total
        return 0.0

@dataclass
class Kline:
    """Candlestick data"""
    symbol: str
    interval: str
    open_time: datetime
    close_time: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    quote_volume: float
    trades: int
    taker_buy_volume: float
    taker_buy_quote_volume: float
    
    @property
    def body(self) -> float:
        """Tamanho do corpo do candle"""
        return abs(self.close_price - self.open_price)
    
    @property
    def upper_shadow(self) -> float:
        """Tamanho da sombra superior"""
        return self.high_price - max(self.open_price, self.close_price)
    
    @property
    def lower_shadow(self) -> float:
        """Tamanho da sombra inferior"""
        return min(self.open_price, self.close_price) - self.low_price
    
    @property
    def is_bullish(self) -> bool:
        """Se o candle é de alta"""
        return self.close_price > self.open_price
    
    @property
    def is_bearish(self) -> bool:
        """Se o candle é de baixa"""
        return self.close_price < self.open_price

@dataclass
class Order:
    """Ordem de trading"""
    order_id: str
    client_order_id: str
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.GTC
    status: OrderStatus = OrderStatus.NEW
    executed_qty: float = 0.0
    cummulative_quote_qty: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    iceberg_qty: Optional[float] = None
    
    @property
    def average_price(self) -> float:
        """Preço médio de execução"""
        if self.executed_qty > 0:
            return self.cummulative_quote_qty / self.executed_qty
        return self.price or 0.0
    
    @property
    def is_filled(self) -> bool:
        """Se a ordem foi totalmente preenchida"""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_active(self) -> bool:
        """Se a ordem está ativa"""
        return self.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED]
    
    @property
    def remaining_qty(self) -> float:
        """Quantidade restante"""
        return self.quantity - self.executed_qty

@dataclass
class AccountInfo:
    """Informações da conta"""
    can_trade: bool
    can_withdraw: bool
    can_deposit: bool
    update_time: datetime
    maker_commission: float
    taker_commission: float
    buyer_commission: float
    seller_commission: float
    balances: Dict[str, Dict[str, float]]  # symbol -> {free, locked, total}
    
    def get_balance(self, asset: str) -> float:
        """Obtém saldo total de um ativo"""
        if asset in self.balances:
            return float(self.balances[asset]['total'])
        return 0.0
    
    def get_free_balance(self, asset: str) -> float:
        """Obtém saldo livre de um ativo"""
        if asset in self.balances:
            return float(self.balances[asset]['free'])
        return 0.0
    
    def get_locked_balance(self, asset: str) -> float:
        """Obtém saldo bloqueado de um ativo"""
        if asset in self.balances:
            return float(self.balances[asset]['locked'])
        return 0.0

class BinanceClient:
    """
    Cliente profissional para API da Binance
    Suporte a REST API e WebSocket com reconexão automática
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None,
                 testnet: bool = False, timeout: int = 30):
        """
        Inicializa o cliente Binance
        
        Args:
            api_key: Chave API (opcional para dados públicos)
            api_secret: Segredo API (opcional para dados públicos)
            testnet: Usar testnet da Binance
            timeout: Timeout para requisições
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout
        
        # Configurar endpoints
        if testnet:
            self.base_url = "https://testnet.binance.vision/api"
            self.ws_url = "wss://testnet.binance.vision/ws"
            self.ws_stream_url = "wss://testnet.binance.vision/stream"
        else:
            self.base_url = "https://api.binance.com/api"
            self.ws_url = "wss://stream.binance.com:9443/ws"
            self.ws_stream_url = "wss://stream.binance.com:9443/stream"
        
        # Sessão HTTP
        self.session: Optional[aiohttp.ClientSession] = None
        
        # WebSocket connections
        self.ws_connections: Dict[str, websockets.WebSocketClientProtocol] = {}
        self.ws_listeners: Dict[str, List[callable]] = {}
        self.ws_reconnect_interval = 5  # segundos
        
        # Cache de dados
        self._cache: Dict[str, Tuple[datetime, Any]] = {}
        self.cache_ttl = {
            'market_data': timedelta(seconds=5),
            'orderbook': timedelta(seconds=2),
            'account_info': timedelta(seconds=30)
        }
        
        # Rate limiting
        self.rate_limits: Dict[str, Dict[str, int]] = {}
        self.last_request_time: Dict[str, datetime] = {}
        
        # Estado
        self.is_connected = False
        self._running = False
        
        logger.info(f"Binance Client inicializado (testnet: {testnet})")
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.disconnect()
    
    async def connect(self):
        """Conecta ao cliente (inicia sessão HTTP)"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        
        self.is_connected = True
        self._running = True
        logger.info("Binance Client conectado")
    
    async def disconnect(self):
        """Desconecta o cliente"""
        self._running = False
        
        # Fechar conexões WebSocket
        for stream_id, ws in self.ws_connections.items():
            try:
                await ws.close()
            except:
                pass
        
        self.ws_connections.clear()
        
        # Fechar sessão HTTP
        if self.session and not self.session.closed:
            await self.session.close()
        
        self.is_connected = False
        logger.info("Binance Client desconectado")
    
    def _sign_request(self, params: Dict[str, Any]) -> str:
        """Assina requisição com HMAC SHA256"""
        if not self.api_secret:
            raise ValueError("API secret não configurada para requisições assinadas")
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _add_timestamp(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Adiciona timestamp aos parâmetros"""
        params['timestamp'] = int(time.time() * 1000)
        return params
    
    async def _make_request(self, method: str, endpoint: str, 
                           signed: bool = False, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Faz requisição HTTP para a API da Binance
        
        Args:
            method: Método HTTP (GET, POST, DELETE)
            endpoint: Endpoint da API
            signed: Se a requisição precisa ser assinada
            **kwargs: Parâmetros adicionais
            
        Returns:
            Resposta JSON ou None em caso de erro
        """
        if not self.session:
            await self.connect()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Preparar parâmetros
        params = kwargs.get('params', {})
        
        if signed:
            if not self.api_key or not self.api_secret:
                raise ValueError("API key e secret necessárias para requisições assinadas")
            
            params = self._add_timestamp(params)
            params['signature'] = self._sign_request(params)
        
        # Headers
        headers = kwargs.get('headers', {})
        if signed and self.api_key:
            headers['X-MBX-APIKEY'] = self.api_key
        
        try:
            # Rate limiting
            await self._check_rate_limit(endpoint)
            
            async with self.session.request(method, url, params=params, headers=headers) as response:
                self._update_rate_limits(response.headers)
                
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Erro HTTP {response.status} em {endpoint}: {error_text}")
                    
                    # Tratamento específico de erros
                    if response.status == 429:
                        logger.warning("Rate limit excedido, aguardando...")
                        await asyncio.sleep(1)
                        return await self._make_request(method, endpoint, signed, **kwargs)
                    
                    return None
        
        except aiohttp.ClientError as e:
            logger.error(f"Erro de conexão em {endpoint}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado em {endpoint}: {e}")
            return None
    
    async def _check_rate_limit(self, endpoint: str):
        """Verifica e respeita rate limits"""
        if endpoint in self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time[endpoint]).total_seconds()
            
            # Regra geral: 1200 requests por minuto
            min_interval = 60 / 1200  # 0.05 segundos entre requests
            
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
        
        self.last_request_time[endpoint] = datetime.now()
    
    def _update_rate_limits(self, headers):
        """Atualiza informações de rate limit dos headers"""
        if 'x-mbx-used-weight' in headers:
            self.rate_limits['used_weight'] = {
                'value': int(headers['x-mbx-used-weight']),
                'timestamp': datetime.now()
            }
        
        if 'x-mbx-order-count-10s' in headers:
            self.rate_limits['order_count_10s'] = {
                'value': int(headers['x-mbx-order-count-10s']),
                'timestamp': datetime.now()
            }
    
    # ===== MARKET DATA METHODS =====
    
    async def get_exchange_info(self) -> Optional[Dict[str, Any]]:
        """Obtém informações da exchange"""
        return await self._make_request('GET', '/v3/exchangeInfo')
    
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Obtém informações de um símbolo específico"""
        exchange_info = await self.get_exchange_info()
        if exchange_info and 'symbols' in exchange_info:
            for sym_info in exchange_info['symbols']:
                if sym_info['symbol'] == symbol:
                    return sym_info
        return None
    
    async def get_ticker(self, symbol: str) -> Optional[MarketData]:
        """Obtém ticker de 24h para um símbolo"""
        cache_key = f"ticker_{symbol}"
        cached = self._get_cached(cache_key, 'market_data')
        if cached:
            return cached
        
        endpoint = '/v3/ticker/24hr'
        params = {'symbol': symbol}
        
        data = await self._make_request('GET', endpoint, params=params)
        if data:
            market_data = self._parse_ticker_data(data)
            self._set_cached(cache_key, market_data, 'market_data')
            return market_data
        
        return None
    
    async def get_tickers(self) -> List[MarketData]:
        """Obtém tickers de todos os símbolos"""
        endpoint = '/v3/ticker/24hr'
        data = await self._make_request('GET', endpoint)
        
        if data and isinstance(data, list):
            tickers = []
            for ticker_data in data:
                try:
                    ticker = self._parse_ticker_data(ticker_data)
                    tickers.append(ticker)
                except Exception as e:
                    logger.debug(f"Erro ao parsear ticker: {e}")
            return tickers
        
        return []
    
    def _parse_ticker_data(self, data: Dict[str, Any]) -> MarketData:
        """Parseia dados de ticker para MarketData"""
        return MarketData(
            symbol=data['symbol'],
            timestamp=datetime.fromtimestamp(data['closeTime'] / 1000),
            bid_price=float(data.get('bidPrice', 0)),
            ask_price=float(data.get('askPrice', 0)),
            last_price=float(data['lastPrice']),
            volume_24h=float(data['volume']),
            high_24h=float(data['highPrice']),
            low_24h=float(data['lowPrice']),
            price_change_24h=float(data['priceChange']),
            price_change_percent_24h=float(data['priceChangePercent']),
            weighted_avg_price=float(data['weightedAvgPrice']),
            open_price=float(data['openPrice']),
            close_price=float(data['lastPrice']),
            quote_volume=float(data['quoteVolume']),
            bid_qty=float(data.get('bidQty', 0)),
            ask_qty=float(data.get('askQty', 0)),
            trades_24h=int(data['count'])
        )
    
    async def get_orderbook(self, symbol: str, limit: int = 100) -> Optional[OrderBook]:
        """Obtém livro de ordens"""
        cache_key = f"orderbook_{symbol}_{limit}"
        cached = self._get_cached(cache_key, 'orderbook')
        if cached:
            return cached
        
        endpoint = '/v3/depth'
        params = {'symbol': symbol, 'limit': limit}
        
        data = await self._make_request('GET', endpoint, params=params)
        if data:
            orderbook = self._parse_orderbook_data(data, symbol)
            self._set_cached(cache_key, orderbook, 'orderbook')
            return orderbook
        
        return None
    
    def _parse_orderbook_data(self, data: Dict[str, Any], symbol: str) -> OrderBook:
        """Parseia dados de orderbook"""
        bids = [(float(price), float(qty)) for price, qty in data['bids']]
        asks = [(float(price), float(qty)) for price, qty in data['asks']]
        
        return OrderBook(
            symbol=symbol,
            timestamp=datetime.now(),
            bids=bids,
            asks=asks
        )
    
    async def get_klines(self, symbol: str, interval: str, 
                        limit: int = 500, start_time: Optional[int] = None,
                        end_time: Optional[int] = None) -> List[Kline]:
        """
        Obtém dados de candlestick (klines)
        
        Args:
            symbol: Símbolo do par
            interval: Intervalo (1m, 5m, 1h, 1d, etc.)
            limit: Número máximo de candles
            start_time: Timestamp de início (opcional)
            end_time: Timestamp de fim (opcional)
        """
        endpoint = '/v3/klines'
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        data = await self._make_request('GET', endpoint, params=params)
        
        if data and isinstance(data, list):
            klines = []
            for kline_data in data:
                try:
                    kline = self._parse_kline_data(kline_data, symbol, interval)
                    klines.append(kline)
                except Exception as e:
                    logger.debug(f"Erro ao parsear kline: {e}")
            return klines
        
        return []
    
    def _parse_kline_data(self, data: List[Any], symbol: str, interval: str) -> Kline:
        """Parseia dados de kline"""
        return Kline(
            symbol=symbol,
            interval=interval,
            open_time=datetime.fromtimestamp(data[0] / 1000),
            close_time=datetime.fromtimestamp(data[6] / 1000),
            open_price=float(data[1]),
            high_price=float(data[2]),
            low_price=float(data[3]),
            close_price=float(data[4]),
            volume=float(data[5]),
            quote_volume=float(data[7]),
            trades=int(data[8]),
            taker_buy_volume=float(data[9]),
            taker_buy_quote_volume=float(data[10])
        )
    
    async def get_historical_klines(self, symbol: str, interval: str, 
                                   start_str: str, end_str: Optional[str] = None) -> List[Kline]:
        """
        Obtém dados históricos de klines
        
        Args:
            symbol: Símbolo do par
            interval: Intervalo
            start_str: Data de início (formato: '1 day ago UTC')
            end_str: Data de fim (opcional)
        """
        # Converter strings para timestamp
        import pandas as pd
        
        start_ts = int(pd.Timestamp(start_str).timestamp() * 1000)
        end_ts = int(pd.Timestamp(end_str).timestamp() * 1000) if end_str else int(time.time() * 1000)
        
        all_klines = []
        current_start = start_ts
        
        # Binance limita a 1000 candles por request
        while current_start < end_ts:
            klines = await self.get_klines(
                symbol=symbol,
                interval=interval,
                limit=1000,
                start_time=current_start,
                end_time=end_ts
            )
            
            if not klines:
                break
            
            all_klines.extend(klines)
            
            # Atualizar start time para próximo batch
            if len(klines) > 0:
                current_start = int(klines[-1].close_time.timestamp() * 1000) + 1
            else:
                break
            
            # Pequena pausa para evitar rate limit
            await asyncio.sleep(0.1)
        
        return all_klines
    
    # ===== ACCOUNT METHODS =====
    
    async def get_account_info(self) -> Optional[AccountInfo]:
        """Obtém informações da conta (requer autenticação)"""
        if not self.api_key or not self.api_secret:
            raise ValueError("Autenticação necessária para informações da conta")
        
        cache_key = "account_info"
        cached = self._get_cached(cache_key, 'account_info')
        if cached:
            return cached
        
        endpoint = '/v3/account'
        data = await self._make_request('GET', endpoint, signed=True)
        
        if data:
            account_info = self._parse_account_info(data)
            self._set_cached(cache_key, account_info, 'account_info')
            return account_info
        
        return None
    
    def _parse_account_info(self, data: Dict[str, Any]) -> AccountInfo:
        """Parseia informações da conta"""
        balances = {}
        for balance in data['balances']:
            asset = balance['asset']
            balances[asset] = {
                'free': float(balance['free']),
                'locked': float(balance['locked']),
                'total': float(balance['free']) + float(balance['locked'])
            }
        
        return AccountInfo(
            can_trade=data['canTrade'],
            can_withdraw=data['canWithdraw'],
            can_deposit=data['canDeposit'],
            update_time=datetime.fromtimestamp(data['updateTime'] / 1000),
            maker_commission=float(data['makerCommission']),
            taker_commission=float(data['takerCommission']),
            buyer_commission=float(data['buyerCommission']),
            seller_commission=float(data['sellerCommission']),
            balances=balances
        )
    
    # ===== ORDER METHODS =====
    
    async def create_order(self, symbol: str, side: OrderSide, 
                          order_type: OrderType, quantity: float,
                          price: Optional[float] = None,
                          time_in_force: TimeInForce = TimeInForce.GTC,
                          stop_price: Optional[float] = None,
                          iceberg_qty: Optional[float] = None,
                          client_order_id: Optional[str] = None) -> Optional[Order]:
        """
        Cria uma nova ordem
        
        Args:
            symbol: Símbolo do par
            side: Lado da ordem (BUY/SELL)
            order_type: Tipo da ordem
            quantity: Quantidade
            price: Preço (obrigatório para ordens LIMIT)
            time_in_force: Tempo de vigência
            stop_price: Preço de stop
            iceberg_qty: Quantidade iceberg
            client_order_id: ID customizado da ordem
            
        Returns:
            Objeto Order ou None em caso de erro
        """
        if not self.api_key or not self.api_secret:
            raise ValueError("Autenticação necessária para criar ordens")
        
        endpoint = '/v3/order'
        
        params = {
            'symbol': symbol,
            'side': side.value,
            'type': order_type.value,
            'quantity': quantity,
            'newOrderRespType': 'FULL'  # Resposta completa
        }
        
        # Adicionar parâmetros opcionais
        if price is not None:
            params['price'] = price
        
        if order_type not in [OrderType.MARKET, OrderType.LIMIT_MAKER]:
            params['timeInForce'] = time_in_force.value
        
        if stop_price is not None:
            params['stopPrice'] = stop_price
        
        if iceberg_qty is not None:
            params['icebergQty'] = iceberg_qty
        
        if client_order_id:
            params['newClientOrderId'] = client_order_id
        else:
            params['newClientOrderId'] = f"r2_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        data = await self._make_request('POST', endpoint, signed=True, params=params)
        
        if data:
            return self._parse_order_data(data)
        
        return None
    
    async def get_order(self, symbol: str, order_id: Optional[str] = None,
                       client_order_id: Optional[str] = None) -> Optional[Order]:
        """
        Obtém status de uma ordem específica
        
        Args:
            symbol: Símbolo do par
            order_id: ID da ordem Binance
            client_order_id: ID customizado da ordem
            
        Returns:
            Objeto Order ou None se não encontrada
        """
        if not self.api_key or not self.api_secret:
            raise ValueError("Autenticação necessária para consultar ordens")
        
        if not order_id and not client_order_id:
            raise ValueError("order_id ou client_order_id é necessário")
        
        endpoint = '/v3/order'
        params = {'symbol': symbol}
        
        if order_id:
            params['orderId'] = order_id
        elif client_order_id:
            params['origClientOrderId'] = client_order_id
        
        data = await self._make_request('GET', endpoint, signed=True, params=params)
        
        if data:
            return self._parse_order_data(data)
        
        return None
    
    async def cancel_order(self, symbol: str, order_id: Optional[str] = None,
                          client_order_id: Optional[str] = None) -> Optional[Order]:
        """
        Cancela uma ordem
        
        Args:
            symbol: Símbolo do par
            order_id: ID da ordem Binance
            client_order_id: ID customizado da ordem
            
        Returns:
            Objeto Order cancelado ou None em caso de erro
        """
        if not self.api_key or not self.api_secret:
            raise ValueError("Autenticação necessária para cancelar ordens")
        
        endpoint = '/v3/order'
        params = {'symbol': symbol}
        
        if order_id:
            params['orderId'] = order_id
        elif client_order_id:
            params['origClientOrderId'] = client_order_id
        else:
            raise ValueError("order_id ou client_order_id é necessário")
        
        data = await self._make_request('DELETE', endpoint, signed=True, params=params)
        
        if data:
            return self._parse_order_data(data)
        
        return None
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        Obtém todas as ordens abertas
        
        Args:
            symbol: Símbolo do par (opcional, se None retorna todas)
            
        Returns:
            Lista de ordens abertas
        """
        if not self.api_key or not self.api_secret:
            raise ValueError("Autenticação necessária para consultar ordens abertas")
        
        endpoint = '/v3/openOrders'
        params = {}
        
        if symbol:
            params['symbol'] = symbol
        
        data = await self._make_request('GET', endpoint, signed=True, params=params)
        
        if data and isinstance(data, list):
            orders = []
            for order_data in data:
                try:
                    order = self._parse_order_data(order_data)
                    orders.append(order)
                except Exception as e:
                    logger.debug(f"Erro ao parsear ordem: {e}")
            return orders
        
        return []
    
    async def get_all_orders(self, symbol: str, limit: int = 500,
                            order_id: Optional[int] = None) -> List[Order]:
        """
        Obtém todas as ordens (incluindo históricas)
        
        Args:
            symbol: Símbolo do par
            limit: Número máximo de ordens
            order_id: ID da ordem para buscar a partir dela
            
        Returns:
            Lista de ordens
        """
        if not self.api_key or not self.api_secret:
            raise ValueError("Autenticação necessária para consultar histórico de ordens")
        
        endpoint = '/v3/allOrders'
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        if order_id:
            params['orderId'] = order_id
        
        data = await self._make_request('GET', endpoint, signed=True, params=params)
        
        if data and isinstance(data, list):
            orders = []
            for order_data in data:
                try:
                    order = self._parse_order_data(order_data)
                    orders.append(order)
                except Exception as e:
                    logger.debug(f"Erro ao parsear ordem: {e}")
            return orders
        
        return []
    
    def _parse_order_data(self, data: Dict[str, Any]) -> Order:
        """Parseia dados de ordem"""
        return Order(
            order_id=str(data['orderId']),
            client_order_id=data['clientOrderId'],
            symbol=data['symbol'],
            side=OrderSide(data['side']),
            type=OrderType(data['type']),
            quantity=float(data['origQty']),
            price=float(data['price']) if data['price'] != '0' else None,
            stop_price=float(data['stopPrice']) if 'stopPrice' in data and data['stopPrice'] != '0' else None,
            time_in_force=TimeInForce(data['timeInForce']) if 'timeInForce' in data else TimeInForce.GTC,
            status=OrderStatus(data['status']),
            executed_qty=float(data['executedQty']),
            cummulative_quote_qty=float(data['cummulativeQuoteQty']),
            created_at=datetime.fromtimestamp(data['time'] / 1000),
            updated_at=datetime.fromtimestamp(data['updateTime'] / 1000),
            iceberg_qty=float(data['icebergQty']) if 'icebergQty' in data and data['icebergQty'] != '0' else None
        )
    
    # ===== WEBSOCKET METHODS =====
    
    async def subscribe_to_stream(self, stream_name: str, callback: callable):
        """
        Inscreve-se em um stream WebSocket
        
        Args:
            stream_name: Nome do stream (ex: 'btcusdt@ticker')
            callback: Função para processar mensagens
        """
        if stream_name not in self.ws_listeners:
            self.ws_listeners[stream_name] = []
        
        self.ws_listeners[stream_name].append(callback)
        
        # Conectar se ainda não estiver conectado
        if stream_name not in self.ws_connections:
            await self._connect_websocket(stream_name)
    
    async def unsubscribe_from_stream(self, stream_name: str, callback: callable):
        """
        Remove inscrição de um stream WebSocket
        """
        if stream_name in self.ws_listeners and callback in self.ws_listeners[stream_name]:
            self.ws_listeners[stream_name].remove(callback)
            
            # Fechar conexão se não houver mais listeners
            if not self.ws_listeners[stream_name]:
                if stream_name in self.ws_connections:
                    await self.ws_connections[stream_name].close()
                    del self.ws_connections[stream_name]
                del self.ws_listeners[stream_name]
    
    async def subscribe_to_ticker(self, symbol: str, callback: callable):
        """Inscreve-se em stream de ticker"""
        stream_name = f"{symbol.lower()}@ticker"
        await self.subscribe_to_stream(stream_name, callback)
    
    async def subscribe_to_kline(self, symbol: str, interval: str, callback: callable):
        """Inscreve-se em stream de kline"""
        stream_name = f"{symbol.lower()}@kline_{interval}"
        await self.subscribe_to_stream(stream_name, callback)
    
    async def subscribe_to_depth(self, symbol: str, callback: callable):
        """Inscreve-se em stream de depth (orderbook)"""
        stream_name = f"{symbol.lower()}@depth"
        await self.subscribe_to_stream(stream_name, callback)
    
    async def subscribe_to_user_data(self, callback: callable):
        """
        Inscreve-se em stream de dados do usuário (ordens, saldos)
        Requer autenticação
        """
        if not self.api_key:
            raise ValueError("API key necessária para user data stream")
        
        # Criar listen key
        endpoint = '/v3/userDataStream'
        data = await self._make_request('POST', endpoint, headers={'X-MBX-APIKEY': self.api_key})
        
        if data and 'listenKey' in data:
            listen_key = data['listenKey']
            stream_name = listen_key
            
            # Iniciar keepalive
            asyncio.create_task(self._keepalive_user_stream(listen_key))
            
            await self.subscribe_to_stream(stream_name, callback)
    
    async def _keepalive_user_stream(self, listen_key: str):
        """Mantém user stream ativo (ping a cada 30 minutos)"""
        while self._running and listen_key in self.ws_listeners:
            try:
                endpoint = '/v3/userDataStream'
                params = {'listenKey': listen_key}
                
                await self._make_request('PUT', endpoint, headers={'X-MBX-APIKEY': self.api_key}, params=params)
                
                await asyncio.sleep(1800)  # 30 minutos
                
            except Exception as e:
                logger.error(f"Erro no keepalive do user stream: {e}")
                await asyncio.sleep(60)
    
    async def _connect_websocket(self, stream_name: str):
        """Conecta a um stream WebSocket"""
        if stream_name in self.ws_connections:
            return
        
        url = f"{self.ws_url}/{stream_name}"
        
        while self._running and stream_name in self.ws_listeners:
            try:
                logger.info(f"Conectando ao WebSocket: {stream_name}")
                
                async with websockets.connect(url) as websocket:
                    self.ws_connections[stream_name] = websocket
                    
                    # Loop de recebimento de mensagens
                    async for message in websocket:
                        if stream_name not in self.ws_listeners:
                            break
                        
                        try:
                            data = json.loads(message)
                            
                            # Notificar listeners
                            if stream_name in self.ws_listeners:
                                for callback in self.ws_listeners[stream_name]:
                                    try:
                                        await callback(data)
                                    except Exception as e:
                                        logger.error(f"Erro no callback WebSocket: {e}")
                        
                        except json.JSONDecodeError as e:
                            logger.error(f"Erro ao decodificar mensagem WebSocket: {e}")
            
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"Conexão WebSocket fechada: {stream_name}")
            except Exception as e:
                logger.error(f"Erro na conexão WebSocket {stream_name}: {e}")
            
            # Tentar reconectar após intervalo
            if self._running and stream_name in self.ws_listeners:
                logger.info(f"Reconectando ao WebSocket em {self.ws_reconnect_interval} segundos...")
                await asyncio.sleep(self.ws_reconnect_interval)
    
    # ===== CACHE METHODS =====
    
    def _get_cached(self, key: str, cache_type: str) -> Optional[Any]:
        """Obtém dados do cache"""
        if key in self._cache:
            timestamp, data = self._cache[key]
            ttl = self.cache_ttl.get(cache_type, timedelta(seconds=1))
            
            if datetime.now() - timestamp < ttl:
                return data
        
        return None
    
    def _set_cached(self, key: str, data: Any, cache_type: str):
        """Armazena dados no cache"""
        self._cache[key] = (datetime.now(), data)
        
        # Limpar cache antigo
        self._clean_cache()
    
    def _clean_cache(self):
        """Limpa entradas antigas do cache"""
        cutoff_time = datetime.now() - timedelta(minutes=5)
        keys_to_remove = []
        
        for key, (timestamp, _) in self._cache.items():
            if timestamp < cutoff_time:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
    
    # ===== UTILITY METHODS =====
    
    async def test_connection(self) -> bool:
        """Testa conexão com a API da Binance"""
        try:
            data = await self._make_request('GET', '/v3/ping')
            return data == {}  # Resposta esperada: {}
        except:
            return False
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Retorna informações de rate limit"""
        info = {}
        
        for limit_type, limit_data in self.rate_limits.items():
            info[limit_type] = {
                'value': limit_data['value'],
                'age': (datetime.now() - limit_data['timestamp']).total_seconds()
            }
        
        return info
    
    async def get_server_time(self) -> Optional[datetime]:
        """Obtém timestamp do servidor Binance"""
        data = await self._make_request('GET', '/v3/time')
        if data and 'serverTime' in data:
            return datetime.fromtimestamp(data['serverTime'] / 1000)
        return None