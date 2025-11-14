import os
import json
import logging
import threading
import time
from typing import Dict, Any
import hmac
import hashlib
import urllib.parse
try:
    import requests
except ImportError:
    requests = None

class CryptoTrading:
    def __init__(self):
        self.is_trading = False
        self.current_strategy = None
        self.logger = logging.getLogger(__name__)

    def start_trading(self, strategy: str, symbol: str = "BTCUSDT", quantity: float = 0.001):
        """Inicia trading automático com estratégia específica."""
        if self.is_trading:
            return "Já está trading em execução"
            
        self.is_trading = True
        self.current_strategy = strategy
        self.logger.info(f"Iniciando trading {strategy} para {symbol}")
        
        # Inicia em thread separada
        thread = threading.Thread(
            target=self._trading_loop,
            args=(strategy, symbol, quantity),
            daemon=True
        )
        thread.start()
        return f"Trading {strategy} iniciado para {symbol}"

    def stop_trading(self):
        """Para o trading automático."""
        self.is_trading = False
        self.current_strategy = None
        return "Trading parado"

    def _trading_loop(self, strategy: str, symbol: str, quantity: float):
        """Loop principal de trading."""
        while self.is_trading:
            try:
                if strategy == "sma":
                    self._sma_strategy(symbol, quantity)
                elif strategy == "rsi":
                    self._rsi_strategy(symbol, quantity)
                
                time.sleep(60)  # Espera 1 minuto entre verificações
            except Exception as e:
                self.logger.error(f"Erro no trading loop: {e}")
                time.sleep(30)

    def _sma_strategy(self, symbol: str, quantity: float):
        """Estratégia Simple Moving Average."""
        # Implementação simplificada - na prática precisaria de dados de mercado
        self.logger.info(f"Executando SMA strategy para {symbol}")
        # Aqui iria a lógica real de trading

    def _rsi_strategy(self, symbol: str, quantity: float):
        """Estratégia RSI."""
        self.logger.info(f"Executando RSI strategy para {symbol}")

def register_crypto_commands(command_system, falar, ouvir_comando):
    """Registra comandos de trading de criptomoedas."""
    trading_engine = CryptoTrading()

    def iniciar_trading_automatico():
        falar("Qual estratégia deseja usar? SMA ou RSI?")
        estrategia = ouvir_comando()
        
        if estrategia and estrategia.lower() in ['sma', 'rsi']:
            resultado = trading_engine.start_trading(estrategia.lower())
            falar(resultado)
        else:
            falar("Estratégia não reconhecida. Use SMA ou RSI.")

    def parar_trading():
        resultado = trading_engine.stop_trading()
        falar(resultado)

    def status_trading():
        if trading_engine.is_trading:
            falar(f"Trading ativo com estratégia {trading_engine.current_strategy}")
        else:
            falar("Trading não está ativo")

    # Registra comandos de trading
    command_system.register_command(
        "iniciar trading", iniciar_trading_automatico, 
        "Inicia trading automático com estratégia SMA ou RSI",
        needs_confirmation=True
    )
    command_system.register_command(
        "parar trading", parar_trading,
        "Para o trading automático"
    )
    command_system.register_command(
        "status trading", status_trading,
        "Mostra status do trading automático"
    )