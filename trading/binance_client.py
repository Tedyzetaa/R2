import hmac
import hashlib
import urllib.parse
import requests
import logging
from typing import Dict, Optional, List
from datetime import datetime

class BinanceClient:
    """Cliente seguro para API Binance"""
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://testnet.binance.vision" if testnet else "https://api.binance.com"
        self.logger = logging.getLogger(__name__)
        
        # Verifica se as chaves foram fornecidas
        if not api_key or not secret_key:
            self.logger.error("Chaves API não fornecidas")
            raise ValueError("Chaves API da Binance não configuradas")
    
    def _generate_signature(self, data: Dict) -> str:
        """Gera assinatura HMAC SHA256"""
        query_string = urllib.parse.urlencode(data)
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def test_connection(self) -> bool:
        """Testa a conexão com a API"""
        try:
            endpoint = "/api/v3/ping"
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Erro ao testar conexão: {e}")
            return False
    
    def get_klines(self, symbol: str, interval: str = '1m', limit: int = 100) -> Optional[List]:
        """Obtém dados de candlestick"""
        try:
            endpoint = "/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
            
            if response.status_code == 401:
                self.logger.error("Erro 401 - Não autorizado. Verifique as chaves API.")
                return None
            elif response.status_code != 200:
                self.logger.error(f"Erro HTTP {response.status_code}: {response.text}")
                return None
                
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Erro ao obter klines: {e}")
            return None
    
    def get_account_info(self) -> Optional[Dict]:
        """Obtém informações da conta"""
        try:
            endpoint = "/api/v3/account"
            params = {
                'timestamp': int(datetime.now().timestamp() * 1000)
            }
            params['signature'] = self._generate_signature(params)
            
            headers = {
                'X-MBX-APIKEY': self.api_key
            }
            
            response = requests.get(
                f"{self.base_url}{endpoint}", 
                params=params, 
                headers=headers, 
                timeout=10
            )
            
            if response.status_code == 401:
                self.logger.error("Erro 401 - Não autorizado. Verifique as chaves API e permissões.")
                return None
            elif response.status_code != 200:
                self.logger.error(f"Erro HTTP {response.status_code}: {response.text}")
                return None
                
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Erro ao obter info da conta: {e}")
            return None
    
    def create_order(self, symbol: str, side: str, quantity: float, order_type: str = "MARKET") -> Optional[Dict]:
        """Cria uma ordem de trading"""
        try:
            endpoint = "/api/v3/order"
            params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity,
                'timestamp': int(datetime.now().timestamp() * 1000)
            }
            params['signature'] = self._generate_signature(params)
            
            headers = {
                'X-MBX-APIKEY': self.api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(
                f"{self.base_url}{endpoint}", 
                data=urllib.parse.urlencode(params),
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 401:
                self.logger.error("Erro 401 - Não autorizado. Verifique permissões de trading.")
                return None
            elif response.status_code != 200:
                self.logger.error(f"Erro HTTP {response.status_code}: {response.text}")
                return None
                
            response.raise_for_status()
            
            self.logger.info(f"Ordem executada: {side} {quantity} {symbol}")
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Erro ao criar ordem: {e}")
            return None
    
    def get_ticker_price(self, symbol: str) -> Optional[float]:
        """Obtém preço atual do símbolo"""
        try:
            endpoint = "/api/v3/ticker/price"
            params = {'symbol': symbol}
            
            response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
            
            if response.status_code == 401:
                self.logger.error("Erro 401 - Não autorizado.")
                return None
            elif response.status_code != 200:
                self.logger.error(f"Erro HTTP {response.status_code}: {response.text}")
                return None
                
            response.raise_for_status()
            data = response.json()
            return float(data['price'])
            
        except Exception as e:
            self.logger.error(f"Erro ao obter preço: {e}")
            return None