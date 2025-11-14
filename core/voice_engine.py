import threading
import time
from typing import Callable, Optional
import logging
import sys

class VoiceEngine:
    def __init__(self, language='pt-BR'):
        self.language = language
        self.is_listening = False
        self.is_speaking = False
        self.callback = None
        self.logger = logging.getLogger(__name__)
        self.has_audio = False
        self.microphone = None
        self.recognizer = None
        self.listener_thread = None
        
        # Inicialização rápida - sem bloqueio
        self._quick_initialize()

    def _quick_initialize(self):
        """Inicialização rápida e não-bloqueante do sistema de voz."""
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            
            # Tenta inicializar o microfone de forma rápida
            try:
                self.microphone = sr.Microphone()
                self.has_audio = True
                self.logger.info("Sistema de voz inicializado (microfone detectado)")
            except OSError as e:
                self.logger.warning(f"Microfone nao disponivel: {e}")
                self.has_audio = False
                
        except ImportError as e:
            self.logger.error(f"SpeechRecognition nao disponivel: {e}")
            self.has_audio = False
        except Exception as e:
            self.logger.error(f"Erro na inicializacao de voz: {e}")
            self.has_audio = False

    def start_listening(self, callback: Callable):
        """Inicia a escuta contínua de forma segura."""
        if not self.has_audio:
            self.logger.warning("Recurso de voz nao disponivel")
            return False
            
        if self.is_listening:
            self.logger.info("Ja esta escutando")
            return True
            
        self.callback = callback
        self.is_listening = True
        
        # Inicia o loop em thread separada
        self.listener_thread = threading.Thread(
            target=self._safe_listen_loop, 
            daemon=True
        )
        self.listener_thread.start()
        self.logger.info("Escuta ativada")
        return True

    def _safe_listen_loop(self):
        """Loop de escuta seguro com tratamento de erros robusto."""
        self.logger.info("Iniciando loop de escuta")
        
        consecutive_errors = 0
        max_errors = 5
        
        while self.is_listening and consecutive_errors < max_errors:
            try:
                # Não processar se estiver falando
                if self.is_speaking:
                    time.sleep(0.1)
                    continue
                    
                text = self._quick_listen()
                if text and self.callback and self.is_listening:
                    self.logger.info(f"Comando detectado: {text}")
                    # Processa em thread separada
                    threading.Thread(
                        target=self._safe_callback,
                        args=(text,),
                        daemon=True
                    ).start()
                    consecutive_errors = 0  # Reset error counter on success
                
                time.sleep(0.1)  # Pequena pausa
                    
            except Exception as e:
                consecutive_errors += 1
                self.logger.error(f"Erro no loop de escuta ({consecutive_errors}/{max_errors}): {e}")
                time.sleep(0.5)  # Pausa maior em caso de erro

        if consecutive_errors >= max_errors:
            self.logger.error("Muitos erros consecutivos - parando escuta")
            self.is_listening = False

        self.logger.info("Loop de escuta finalizado")

    def _quick_listen(self) -> Optional[str]:
        """Escuta rápida com timeout curto."""
        if not self.has_audio or not self.microphone or not self.is_listening:
            return None
            
        try:
            import speech_recognition as sr
            
            with self.microphone as source:
                # Ajuste rápido de ruído
                self.recognizer.adjust_for_ambient_noise(source, duration=0.1)
                
                # Escuta ultra-rápida
                audio = self.recognizer.listen(source, timeout=0.5, phrase_time_limit=2)
            
            text = self.recognizer.recognize_google(audio, language=self.language)
            return text.lower().strip()
            
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            if "timeout" not in str(e).lower():
                self.logger.debug(f"Erro na escuta: {e}")
            return None

    def _safe_callback(self, text: str):
        """Callback seguro com tratamento de erro."""
        try:
            if self.callback and self.is_listening:
                self.callback(text)
        except Exception as e:
            self.logger.error(f"Erro no callback: {e}")

    def stop_listening(self):
        """Para a escuta de forma imediata e segura."""
        if self.is_listening:
            self.is_listening = False
            self.logger.info("Escuta parada")
        else:
            self.logger.debug("Escuta ja estava parada")

    def set_speaking_status(self, speaking: bool):
        """Controla o status de fala para evitar eco."""
        self.is_speaking = speaking
        self.logger.debug(f"Status de fala alterado para: {speaking}")

    def listen_once(self) -> Optional[str]:
        """Escuta única para comandos que precisam de resposta."""
        return self._quick_listen()

    def is_audio_available(self) -> bool:
        return self.has_audio

    def get_listening_status(self) -> bool:
        return self.is_listening