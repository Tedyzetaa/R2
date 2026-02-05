import os
import shutil

# Código corrigido para audio_processor.py
AUDIO_PROCESSOR_CODE = '''import os
import subprocess
import tempfile
from gtts import gTTS
import logging
from typing import Optional

class AudioProcessor:
    def __init__(self, lang='pt', use_audio=True):
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
            
        try:
            # Cria arquivo temporário
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Gera áudio com gTTS
            tts = gTTS(text=text, lang=self.lang, slow=False)
            tts.save(temp_path)
            
            # Tenta reproduzir com ffplay primeiro (mais confiável)
            if self.has_ffplay:
                return self._play_with_ffplay(temp_path)
            # Fallback para pygame
            elif self.has_pygame:
                return self._play_with_pygame(temp_path)
            else:
                self.logger.warning("Nenhum reprodutor de áudio disponível. Modo texto ativado.")
                print(f"R2: {text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro na síntese de voz: {e}")
            print(f"R2: {text}")
            return False
        finally:
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
                ['ffplay', '-nodisp', '-autoexit', file_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Erro no ffplay: {e}")
            return False
        except FileNotFoundError:
            self.logger.warning("ffplay não encontrado.")
            self.has_ffplay = False
            return False

    def _play_with_pygame(self, file_path: str) -> bool:
        """Reproduz áudio usando pygame."""
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Espera terminar de tocar
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
                
            return True
        except Exception as e:
            self.logger.error(f"Erro no pygame: {e}")
            return False

    def is_audio_available(self) -> bool:
        """Verifica se a reprodução de áudio está disponível."""
        return self.use_audio and (self.has_ffplay or self.has_pygame)
'''

def fix_audio_processor():
    """Corrige o arquivo audio_processor.py"""
    audio_file = os.path.join('core', 'audio_processor.py')
    
    try:
        with open(audio_file, 'w', encoding='utf-8') as f:
            f.write(AUDIO_PROCESSOR_CODE)
        print(f"✅ {audio_file} corrigido com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao corrigir {audio_file}: {e}")
        return False

if __name__ == "__main__":
    print("Corrigindo audio_processor.py...")
    if fix_audio_processor():
        print("🎉 Correção aplicada! Agora execute: python main.py")
    else:
        print("⚠️  Falha na correção.")