import threading
import time
import queue
import json
import logging
from typing import Callable, Optional
import sys
import os

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
        
        # Inicialização do Vosk
        self.vosk_model = None
        self.vosk_recognizer = None
        self.audio_stream = None
        self.pyaudio_instance = None
        self.audio_queue = queue.Queue()
        
        self._initialize_vosk()

    def _initialize_vosk(self):
        """Inicializa o modelo Vosk para reconhecimento offline."""
        try:
            from vosk import Model, KaldiRecognizer
            import pyaudio
            
            # Caminho do modelo Vosk em português
            model_path = "./model/vosk-model-small-pt-0.3"
            
            if not os.path.exists(model_path):
                self.logger.error(f"Modelo Vosk não encontrado em: {model_path}")
                self.logger.info("Por favor, baixe o modelo em: https://alphacephei.com/vosk/models")
                self.has_audio = False
                return
            
            self.vosk_model = Model(model_path)
            self.pyaudio_instance = pyaudio.PyAudio()
            self.has_audio = True
            self.logger.info("✅ Sistema de voz Vosk inicializado com sucesso")
            
        except ImportError as e:
            self.logger.error(f"Bibliotecas Vosk/PyAudio não disponíveis: {e}")
            self.has_audio = False
        except Exception as e:
            self.logger.error(f"Erro na inicialização do Vosk: {e}")
            self.has_audio = False

    def start_listening(self, callback: Callable):
        """Inicia a escuta contínua com Vosk."""
        if not self.has_audio or not self.vosk_model:
            self.logger.warning("Sistema de voz Vosk não disponível")
            return False
            
        if self.is_listening:
            self.logger.info("Já está escutando")
            return True
            
        self.callback = callback
        self.is_listening = True
        
        # Inicia o loop em thread separada
        self.listener_thread = threading.Thread(
            target=self._vosk_listen_loop, 
            daemon=True
        )
        self.listener_thread.start()
        self.logger.info("🎤 Escuta Vosk ativada")
        return True

    def _vosk_listen_loop(self):
        """Loop de escuta usando Vosk."""
        import pyaudio
        from vosk import KaldiRecognizer
        
        try:
            # Configuração do PyAudio para Vosk
            self.vosk_recognizer = KaldiRecognizer(self.vosk_model, 16000)
            
            self.audio_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=4096,
                stream_callback=self._audio_callback
            )
            
            self.audio_stream.start_stream()
            self.logger.info("Stream de áudio Vosk iniciado")
            
            consecutive_errors = 0
            max_errors = 5
            
            while self.is_listening and consecutive_errors < max_errors:
                try:
                    # Não processar se estiver falando
                    if self.is_speaking:
                        time.sleep(0.1)
                        continue
                    
                    # Processa áudio da queue
                    if not self.audio_queue.empty():
                        data = self.audio_queue.get()
                        
                        if self.vosk_recognizer.AcceptWaveform(data):
                            result = json.loads(self.vosk_recognizer.Result())
                            text = result.get('text', '').strip()
                            
                            if text and self.callback and self.is_listening:
                                self.logger.info(f"Comando Vosk detectado: {text}")
                                # Processa em thread separada
                                threading.Thread(
                                    target=self._safe_callback,
                                    args=(text,),
                                    daemon=True
                                ).start()
                                consecutive_errors = 0
                    
                    time.sleep(0.1)
                        
                except Exception as e:
                    consecutive_errors += 1
                    self.logger.error(f"Erro no loop Vosk ({consecutive_errors}/{max_errors}): {e}")
                    time.sleep(0.5)

            if consecutive_errors >= max_errors:
                self.logger.error("Muitos erros consecutivos - parando escuta Vosk")
                self.is_listening = False

        except Exception as e:
            self.logger.error(f"Erro crítico no loop Vosk: {e}")
            self.is_listening = False
        finally:
            self._cleanup_vosk_audio()

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback para captura de áudio do PyAudio."""
        if self.is_listening:
            self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)

    def _cleanup_vosk_audio(self):
        """Limpa recursos de áudio do Vosk."""
        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            self.logger.info("Recursos de áudio Vosk liberados")
        except Exception as e:
            self.logger.error(f"Erro ao limpar recursos de áudio: {e}")

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
            self._cleanup_vosk_audio()
            self.logger.info("Escuta Vosk parada")
        else:
            self.logger.debug("Escuta já estava parada")

    def set_speaking_status(self, speaking: bool):
        """Controla o status de fala para evitar eco."""
        self.is_speaking = speaking
        self.logger.debug(f"Status de fala alterado para: {speaking}")

    def listen_once(self) -> Optional[str]:
        """Escuta única para comandos que precisam de resposta (usando método antigo como fallback)."""
        if not self.has_audio:
            return None
            
        try:
            import speech_recognition as sr
            
            with sr.Microphone() as source:
                recognizer = sr.Recognizer()
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
            text = recognizer.recognize_google(audio, language=self.language)
            return text.lower().strip()
            
        except Exception as e:
            self.logger.debug(f"Erro na escuta única: {e}")
            return None

    def is_audio_available(self) -> bool:
        return self.has_audio

    def get_listening_status(self) -> bool:
        return self.is_listening

    def __del__(self):
        """Destrutor para limpeza de recursos."""
        self.stop_listening()
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()