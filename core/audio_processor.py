import os
import subprocess
import tempfile
from gtts import gTTS
import logging
import threading
import time
from typing import Optional

class AudioProcessor:
    def __init__(self, voice_engine=None, lang='pt', use_audio=True):
        self.voice_engine = voice_engine
        self.lang = lang
        self.use_audio = use_audio
        self.logger = logging.getLogger(__name__)
        self.has_ffplay = False
        self.has_pygame = False
        self._check_audio_dependencies()

    def _check_audio_dependencies(self):
        """Verifica se as dependências de áudio estão disponíveis."""
        if not self.use_audio:
            return
            
        # Verifica se ffplay está disponível (parte do ffmpeg)
        try:
            result = subprocess.run(['ffplay', '-version'], 
                                  capture_output=True, 
                                  text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            self.has_ffplay = result.returncode == 0
            if self.has_ffplay:
                self.logger.info("ffplay disponível para reprodução de áudio")
        except FileNotFoundError:
            self.has_ffplay = False
            self.logger.warning("ffplay não encontrado. Instale o ffmpeg para melhor qualidade de áudio.")
        
        # Verifica se pygame está disponível como alternativa
        try:
            import pygame
            pygame.mixer.init()
            self.has_pygame = True
            self.logger.info("Pygame disponível para reprodução de áudio")
        except ImportError:
            self.has_pygame = False
            self.logger.warning("Pygame não disponível.")

    def text_to_speech(self, text: str) -> bool:
        """Converte texto em fala usando gTTS e reproduz."""
        if not self.use_audio:
            self.logger.info(f"TTS (modo texto): {text}")
            return True
            
        # Executa em thread separada para não travar a interface
        thread = threading.Thread(target=self._speak_thread, args=(text,), daemon=True)
        thread.start()
        return True

    def _speak_thread(self, text: str):
        """Thread separada para síntese de voz."""
        try:
            # 🔥 Pausa a escuta durante a fala para evitar eco
            if self.voice_engine:
                self.voice_engine.set_speaking_status(True)

            # Cria arquivo temporário
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Gera áudio com gTTS
            self.logger.info(f"Gerando áudio para: {text}")
            tts = gTTS(text=text, lang=self.lang, slow=False)
            tts.save(temp_path)
            self.logger.info("Áudio gerado com sucesso")
            
            # Tenta reproduzir com ffplay primeiro (mais confiável)
            if self.has_ffplay:
                success = self._play_with_ffplay(temp_path)
            # Fallback para pygame
            elif self.has_pygame:
                success = self._play_with_pygame(temp_path)
            else:
                self.logger.warning("Nenhum reprodutor de áudio disponível.")
                print(f"R2: {text}")  # Fallback para texto
                success = False
                
            if success:
                self.logger.info("Áudio reproduzido com sucesso")
            else:
                self.logger.warning("Falha na reprodução de áudio")
                
        except Exception as e:
            self.logger.error(f"Erro na síntese de voz: {e}")
            print(f"R2: {text}")  # Fallback para texto
        finally:
            # 🔥 Reativa a escuta após a fala
            if self.voice_engine:
                self.voice_engine.set_speaking_status(False)
                
            # Limpa arquivo temporário
            try:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                self.logger.warning(f"Erro ao limpar arquivo temporário: {e}")

    def _play_with_ffplay(self, file_path: str) -> bool:
        """Reproduz áudio usando ffplay."""
        try:
            result = subprocess.run(
                ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', file_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=30  # Timeout para evitar travamento
            )
            return True
        except subprocess.TimeoutExpired:
            self.logger.error("ffplay timeout - processo travado")
            return False
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Erro no ffplay: {e}")
            return False
        except FileNotFoundError:
            self.logger.warning("ffplay não encontrado.")
            self.has_ffplay = False
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado no ffplay: {e}")
            return False

    def _play_with_pygame(self, file_path: str) -> bool:
        """Reproduz áudio usando pygame."""
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Espera terminar de tocar com timeout
            start_time = time.time()
            while pygame.mixer.music.get_busy():
                if time.time() - start_time > 30:  # Timeout de 30 segundos
                    pygame.mixer.music.stop()
                    self.logger.warning("Pygame timeout - parando música")
                    return False
                time.sleep(0.1)
                
            return True
        except Exception as e:
            self.logger.error(f"Erro no pygame: {e}")
            return False

    def is_audio_available(self) -> bool:
        """Verifica se a reprodução de áudio está disponível."""
        return self.use_audio and (self.has_ffplay or self.has_pygame)