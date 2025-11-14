#!/usr/bin/env python3
"""
R2 - Assistente Pessoal Completo com Trading Automático
"""

import os
import sys
import logging

# Adiciona diretórios ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'commands'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'gui'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'trading'))

from core.voice_engine import VoiceEngine
from core.audio_processor import AudioProcessor
from core.command_system import CommandSystem
from commands.system_commands import register_system_commands
from commands.web_commands import register_web_commands
from commands.basic_commands import register_basic_commands
from commands.crypto_commands import register_crypto_commands
from gui.assistant_gui import AssistantGUI
from config.settings import Settings

# Tentar importar módulo de trading
try:
    from trading.binance_client import BinanceClient
    from trading.trading_engine import TradingEngine
    TRADING_AVAILABLE = True
except ImportError as e:
    print(f"Módulo de trading não disponível: {e}")
    TRADING_AVAILABLE = False

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('r2_assistant.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

class R2Assistant:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Valida configurações
        Settings.validate_apis()
        
        # Inicializa componentes principais
        self.voice_engine = VoiceEngine(language=Settings.LANGUAGE)
        self.audio_processor = AudioProcessor(
            voice_engine=self.voice_engine,
            lang=Settings.LANGUAGE.split('-')[0],
            use_audio=Settings.USE_AUDIO
        )
        self.command_system = CommandSystem()
        
        # Inicializa trading engine se disponível - COM VERIFICAÇÃO DE CONEXÃO
        self.trading_engine = None
        if TRADING_AVAILABLE and Settings.BINANCE_API_KEY and Settings.BINANCE_SECRET_KEY:
            try:
                binance_client = BinanceClient(
                    Settings.BINANCE_API_KEY,
                    Settings.BINANCE_SECRET_KEY,
                    Settings.TESTNET
                )
                
                # Testa a conexão antes de inicializar o trading engine
                self.logger.info("Testando conexão com Binance...")
                if binance_client.test_connection():
                    self.trading_engine = TradingEngine(binance_client)
                    self.logger.info("✅ Trading Engine inicializado com sucesso")
                else:
                    self.logger.error("❌ Falha na conexão com Binance. Verifique as chaves API.")
                    print("\n🔧 SOLUÇÃO RÁPIDA:")
                    print("1. Execute: python test_binance.py")
                    print("2. Verifique as chaves API no arquivo .env")
                    print("3. Use chaves da TESTNET: https://testnet.binance.vision/")
                    
            except Exception as e:
                self.logger.error(f"Erro ao inicializar Trading Engine: {e}")
                print(f"❌ Erro detalhado: {e}")
        
        # Registra comandos
        self._register_commands()
        
        # Interface
        self.gui = AssistantGUI(
            self.command_system,
            self.audio_processor,
            self.voice_engine,
            self.trading_engine
        )

    def _register_commands(self):
        """Registra todos os comandos disponíveis."""
        register_system_commands(
            self.command_system,
            self.audio_processor.text_to_speech,
            self.voice_engine.listen_once
        )
        
        register_web_commands(
            self.command_system,
            self.audio_processor.text_to_speech,
            self.voice_engine.listen_once
        )
        
        register_basic_commands(
            self.command_system,
            self.audio_processor.text_to_speech,
            self.voice_engine.listen_once
        )
        
        register_crypto_commands(
            self.command_system,
            self.audio_processor.text_to_speech,
            self.voice_engine.listen_once,
            self.trading_engine
        )

    def run(self):
        """Inicia o assistente."""
        self.logger.info("Iniciando R2 Assistant...")
        try:
            self.gui.run()
        except KeyboardInterrupt:
            self.logger.info("R2 finalizado")
        except Exception as e:
            self.logger.error(f"Erro: {e}")
        finally:
            if self.trading_engine:
                self.trading_engine.stop_auto_trading()
            self.voice_engine.stop_listening()

if __name__ == "__main__":
    assistant = R2Assistant()
    assistant.run()