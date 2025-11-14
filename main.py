#!/usr/bin/env python3
"""
R2 - Assistente Pessoal Completo
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

from core.voice_engine import VoiceEngine
from core.audio_processor import AudioProcessor
from core.command_system import CommandSystem
from commands.system_commands import register_system_commands
from commands.web_commands import register_web_commands
from commands.basic_commands import register_basic_commands
from gui.assistant_gui import AssistantGUI
from config.settings import Settings

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

class R2Assistant:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Valida configurações
        Settings.validate_apis()
        
        # Inicializa componentes
        self.voice_engine = VoiceEngine(language=Settings.LANGUAGE)
        self.audio_processor = AudioProcessor(
            voice_engine=self.voice_engine,
            lang=Settings.LANGUAGE.split('-')[0],
            use_audio=Settings.USE_AUDIO
        )
        self.command_system = CommandSystem()
        
        # Registra comandos
        self._register_commands()
        
        # Interface
        self.gui = AssistantGUI(
            self.command_system,
            self.audio_processor,
            self.voice_engine
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
            self.voice_engine.stop_listening()

if __name__ == "__main__":
    assistant = R2Assistant()
    assistant.run()