import threading
import queue
import json
import logging
from typing import Callable, Optional
import pyaudio
from vosk import Model, KaldiRecognizer

class VoskEngine:
    """
    Motor de reconhecimento de voz offline usando Vosk.
    Pode ser usado como alternativa ou complemento ao VoiceEngine principal.
    """
    
    def __init__(self, model_path: str = "./model/vosk-model-small-pt-0.3"):
        self.logger = logging.getLogger(__name__)
        self.model_path = model_path
        self.is_listening = False
        self.callback = None
        self.audio_queue = queue.Queue()
        
        # Componentes Vosk
        self.model = None
        self.recognizer = None
        self.pyaudio = None
        self.stream = None
        
        self._initialize_model()

    def _initialize_model(self):
        """Inicializa o modelo Vosk."""
        try:
            if not os.path.exists(self.model_path):
                self.logger.error(f"Modelo Vosk não encontrado em: {self.model_path}")
                return False
                
            self.model = Model(self.model_path)
            self.pyaudio = pyaudio.PyAudio()
            self.logger.info("✅ Modelo Vosk carregado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo Vosk: {e}")
            return False

    def start_listening(self, callback: Callable) -> bool:
        """Inicia a escuta contínua."""
        if not self.model:
            self.logger.error("Modelo Vosk não inicializado")
            return False
            
        self.callback = callback
        self.is_listening = True
        
        # Configura stream de áudio
        self.stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=4096,
            stream_callback=self._audio_callback
        )
        
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.stream.start_stream()
        
        # Thread de processamento
        self.process_thread = threading.Thread(
            target=self._process_audio,
            daemon=True
        )
        self.process_thread.start()
        
        self.logger.info("🎤 Escuta Vosk iniciada")
        return True

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback para captura de áudio."""
        if self.is_listening:
            self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)

    def _process_audio(self):
        """Processa o áudio capturado."""
        while self.is_listening:
            try:
                if not self.audio_queue.empty():
                    data = self.audio_queue.get()
                    
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get('text', '').strip()
                        
                        if text and self.callback:
                            self.logger.info(f"Comando reconhecido: {text}")
                            threading.Thread(
                                target=self.callback,
                                args=(text,),
                                daemon=True
                            ).start()
                
            except Exception as e:
                self.logger.error(f"Erro no processamento de áudio: {e}")

    def stop_listening(self):
        """Para a escuta."""
        self.is_listening = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.logger.info("Escuta Vosk parada")

    def listen_once(self, timeout: int = 5) -> Optional[str]:
        """Escuta por um único comando com timeout."""
        if not self.model:
            return None
            
        import time
        start_time = time.time()
        
        stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=4096
        )
        
        recognizer = KaldiRecognizer(self.model, 16000)
        
        try:
            while time.time() - start_time < timeout:
                data = stream.read(4096, exception_on_overflow=False)
                
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get('text', '').strip()
                    if text:
                        stream.stop_stream()
                        stream.close()
                        return text
        except Exception as e:
            self.logger.error(f"Erro na escuta única: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            
        return None

    def __del__(self):
        """Limpeza de recursos."""
        self.stop_listening()
        if self.pyaudio:
            self.pyaudio.terminate()