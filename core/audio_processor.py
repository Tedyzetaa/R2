import os
import subprocess
import tempfile
from gtts import gTTS
import logging
import threading
import time
import queue
from typing import Optional

# Importação condicional do pyttsx3
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

class AudioProcessor:
    def __init__(self, voice_engine=None, lang='pt', use_audio=True, voice_type='online'):
        self.voice_engine = voice_engine
        self.lang = lang
        self.use_audio = use_audio
        self.voice_type = voice_type
        self.logger = logging.getLogger(__name__)
        self.has_ffplay = False
        self.has_pygame = False
        self.pyttsx3_engine = None
        self._tts_queue = queue.Queue()
        self._tts_working = False
        self._current_voice_settings = {
            'rate': 150,
            'volume': 0.8,
            'voice_index': 0
        }
        
        self._check_audio_dependencies()
        
        # Inicializa pyttsx3 se solicitado
        if self.voice_type == 'offline' and PYTTSX3_AVAILABLE:
            self._initialize_pyttsx3()

    def _initialize_pyttsx3(self):
        """Inicializa o motor pyttsx3 para TTS offline com tratamento de erros."""
        try:
            self.pyttsx3_engine = pyttsx3.init()
            
            # 🔧 CONFIGURAÇÕES DE VOZ - COM TRATAMENTO DE ERROS
            self._configure_voice_safe()
            
            # Inicia thread de processamento de TTS
            self._tts_working = True
            self._tts_thread = threading.Thread(
                target=self._tts_worker, 
                daemon=True,
                name="TTS_Worker"
            )
            self._tts_thread.start()
            
            self.logger.info("✅ Pyttsx3 inicializado para TTS offline")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar pyttsx3: {e}")
            self.voice_type = 'online'  # Fallback para gTTS

    def _configure_voice_safe(self):
        """Configura a voz do pyttsx3 com tratamento robusto de erros."""
        if not self.pyttsx3_engine:
            return
            
        try:
            # 🔥 LISTA TODAS AS VOZES DISPONÍVEIS
            voices = self.pyttsx3_engine.getProperty('voices')
            self.logger.info("Voices disponíveis:")
            for i, voice in enumerate(voices):
                self.logger.info(f"  {i}: {voice.name} - {voice.id}")
            
            # 🎯 CONFIGURAÇÃO DA VOZ - COM FALLBACKS
            voice_found = False
            
            # OPÇÃO 1: Voz em português (se disponível)
            for i, voice in enumerate(voices):
                if 'portuguese' in voice.name.lower() or 'português' in voice.name.lower() or 'pt' in voice.name.lower():
                    try:
                        self.pyttsx3_engine.setProperty('voice', voice.id)
                        self._current_voice_settings['voice_index'] = i
                        self.logger.info(f"✅ Voz em português selecionada: {voice.name}")
                        voice_found = True
                        break
                    except Exception as e:
                        self.logger.warning(f"Erro ao selecionar voz {voice.name}: {e}")
                        continue
            
            # OPÇÃO 2: Primeira voz feminina disponível
            if not voice_found:
                for i, voice in enumerate(voices):
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower() or 'maria' in voice.name.lower():
                        try:
                            self.pyttsx3_engine.setProperty('voice', voice.id)
                            self._current_voice_settings['voice_index'] = i
                            self.logger.info(f"✅ Voz feminina selecionada: {voice.name}")
                            voice_found = True
                            break
                        except Exception as e:
                            continue
            
            # OPÇÃO 3: Primeira voz disponível
            if not voice_found and voices:
                try:
                    self.pyttsx3_engine.setProperty('voice', voices[0].id)
                    self._current_voice_settings['voice_index'] = 0
                    self.logger.info(f"✅ Voz padrão selecionada: {voices[0].name}")
                    voice_found = True
                except Exception as e:
                    self.logger.error(f"Erro ao selecionar voz padrão: {e}")
            
            # ⚙️ AJUSTES DE QUALIDADE DA VOZ - COM TRATAMENTO DE ERROS
            try:
                self.pyttsx3_engine.setProperty('rate', self._current_voice_settings['rate'])
                self.logger.info(f"Velocidade configurada: {self._current_voice_settings['rate']}")
            except Exception as e:
                self.logger.warning(f"Não foi possível configurar velocidade: {e}")
            
            try:
                self.pyttsx3_engine.setProperty('volume', self._current_voice_settings['volume'])
                self.logger.info(f"Volume configurado: {self._current_voice_settings['volume']}")
            except Exception as e:
                self.logger.warning(f"Não foi possível configurar volume: {e}")
            
            # 🔥 EVITA CONFIGURAR PITCH NO WINDOWS (não suportado)
            if os.name != 'nt':  # Não é Windows
                try:
                    self.pyttsx3_engine.setProperty('pitch', 110)
                except Exception as e:
                    self.logger.warning(f"Não foi possível configurar tom: {e}")
            else:
                self.logger.info("⚠️  Ajuste de tom não suportado no Windows SAPI5")
                
        except Exception as e:
            self.logger.error(f"Erro crítico ao configurar voz: {e}")

    def _tts_worker(self):
        """Worker thread para processar TTS em sequência."""
        while self._tts_working:
            try:
                # Aguarda por texto para falar
                text, event = self._tts_queue.get(timeout=1.0)
                
                if text is None:  # Sinal para parar
                    break
                    
                try:
                    self.logger.info(f"Reproduzindo com pyttsx3: {text}")
                    
                    # 🔥 Pausa a escuta durante a fala
                    if self.voice_engine:
                        self.voice_engine.set_speaking_status(True)
                    
                    # Fala o texto
                    self.pyttsx3_engine.say(text)
                    self.pyttsx3_engine.runAndWait()
                    
                    # Pequena pausa entre falas
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"Erro ao falar texto: {e}")
                    # Fallback para online
                    self._speak_online_thread(text)
                finally:
                    # 🔥 Reativa a escuta após a fala
                    if self.voice_engine:
                        self.voice_engine.set_speaking_status(False)
                    
                    # Sinaliza que terminou
                    if event:
                        event.set()
                        
                self._tts_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Erro no worker TTS: {e}")
                time.sleep(1.0)

    def _check_audio_dependencies(self):
        """Verifica se as dependências de áudio estão disponíveis."""
        if not self.use_audio:
            return
            
        # Verifica se ffplay está disponível
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
            self.logger.warning("ffplay não encontrado.")
        
        # Verifica se pygame está disponível
        try:
            import pygame
            pygame.mixer.init()
            self.has_pygame = True
            self.logger.info("Pygame disponível para reprodução de áudio")
        except ImportError:
            self.has_pygame = False

    def text_to_speech(self, text: str) -> bool:
        """Converte texto em fala usando o método selecionado."""
        if not self.use_audio:
            self.logger.info(f"TTS (modo texto): {text}")
            return True
            
        # Escolhe o método de TTS baseado na configuração
        if self.voice_type == 'offline' and self.pyttsx3_engine and self._tts_working:
            return self._offline_tts(text)
        else:
            return self._online_tts(text)

    def _online_tts(self, text: str) -> bool:
        """Usa gTTS (online) para síntese de voz."""
        thread = threading.Thread(
            target=self._speak_online_thread, 
            args=(text,), 
            daemon=True,
            name="Online_TTS"
        )
        thread.start()
        return True

    def _speak_online_thread(self, text: str):
        """Thread separada para síntese de voz online."""
        try:
            if self.voice_engine:
                self.voice_engine.set_speaking_status(True)

            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name

            # gTTS com configurações de qualidade
            tts = gTTS(text=text, lang=self.lang, slow=False)
            tts.save(temp_path)
            self.logger.info("Áudio gerado com sucesso via gTTS")

            if self.has_ffplay:
                success = self._play_with_ffplay(temp_path)
            elif self.has_pygame:
                success = self._play_with_pygame(temp_path)
            else:
                self.logger.warning("Nenhum reprodutor de áudio disponível.")
                print(f"R2: {text}")
                success = False

            if success:
                self.logger.info("Áudio reproduzido com sucesso")
            else:
                self.logger.warning("Falha na reprodução de áudio")

        except Exception as e:
            self.logger.error(f"Erro na síntese de voz online: {e}")
            print(f"R2: {text}")
        finally:
            if self.voice_engine:
                self.voice_engine.set_speaking_status(False)
            try:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                self.logger.warning(f"Erro ao limpar arquivo temporário: {e}")

    def _offline_tts(self, text: str) -> bool:
        """Usa pyttsx3 (offline) para síntese de voz via fila."""
        if not self._tts_working:
            return self._online_tts(text)  # Fallback para online
            
        try:
            # Cria evento para sincronização (opcional)
            event = threading.Event()
            
            # Adiciona à fila
            self._tts_queue.put((text, event))
            
            # Espera até ser processado (timeout de 30 segundos)
            # event.wait(timeout=30.0)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar texto à fila TTS: {e}")
            return self._online_tts(text)  # Fallback para online

    def _play_with_ffplay(self, file_path: str) -> bool:
        try:
            result = subprocess.run(
                ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', file_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=30
            )
            return True
        except Exception as e:
            self.logger.error(f"Erro no ffplay: {e}")
            return False

    def _play_with_pygame(self, file_path: str) -> bool:
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            start_time = time.time()
            while pygame.mixer.music.get_busy():
                if time.time() - start_time > 30:
                    pygame.mixer.music.stop()
                    return False
                time.sleep(0.1)
            return True
        except Exception as e:
            self.logger.error(f"Erro no pygame: {e}")
            return False

    # 🔧 MÉTODOS PARA PERSONALIZAÇÃO DA VOZ EM TEMPO REAL
    def set_voice_rate(self, rate: int):
        """Altera a velocidade da voz (apenas offline)."""
        if self.pyttsx3_engine:
            try:
                self.pyttsx3_engine.setProperty('rate', rate)
                self._current_voice_settings['rate'] = rate
                self.logger.info(f"Velocidade da voz alterada para: {rate}")
            except Exception as e:
                self.logger.error(f"Erro ao alterar velocidade: {e}")

    def set_voice_volume(self, volume: float):
        """Altera o volume da voz (apenas offline)."""
        if self.pyttsx3_engine:
            try:
                self.pyttsx3_engine.setProperty('volume', max(0.0, min(1.0, volume)))
                self._current_voice_settings['volume'] = volume
                self.logger.info(f"Volume da voz alterado para: {volume}")
            except Exception as e:
                self.logger.error(f"Erro ao alterar volume: {e}")

    def set_voice_pitch(self, pitch: int):
        """Altera o tom da voz (apenas offline)."""
        # ⚠️ Não suportado no Windows SAPI5
        if self.pyttsx3_engine and os.name != 'nt':
            try:
                self.pyttsx3_engine.setProperty('pitch', pitch)
                self.logger.info(f"Tom da voz alterado para: {pitch}")
            except Exception as e:
                self.logger.warning(f"Tom não suportado: {e}")

    def list_available_voices(self):
        """Lista todas as vozes disponíveis."""
        if self.pyttsx3_engine:
            try:
                voices = self.pyttsx3_engine.getProperty('voices')
                voice_list = []
                for i, voice in enumerate(voices):
                    voice_list.append({
                        'index': i,
                        'name': voice.name,
                        'id': voice.id,
                        'languages': getattr(voice, 'languages', [])
                    })
                return voice_list
            except Exception as e:
                self.logger.error(f"Erro ao listar vozes: {e}")
        return []

    def change_voice(self, voice_index: int):
        """Altera para uma voz específica."""
        if self.pyttsx3_engine:
            try:
                voices = self.pyttsx3_engine.getProperty('voices')
                if 0 <= voice_index < len(voices):
                    self.pyttsx3_engine.setProperty('voice', voices[voice_index].id)
                    self._current_voice_settings['voice_index'] = voice_index
                    self.logger.info(f"Voz alterada para: {voices[voice_index].name}")
                    return True
            except Exception as e:
                self.logger.error(f"Erro ao alterar voz: {e}")
        return False

    def stop_tts(self):
        """Para o sistema TTS e limpa recursos."""
        self._tts_working = False
        try:
            # Sinaliza para a thread parar
            self._tts_queue.put((None, None))
            
            # Limpa a fila
            while not self._tts_queue.empty():
                try:
                    self._tts_queue.get_nowait()
                    self._tts_queue.task_done()
                except queue.Empty:
                    break
                    
        except Exception as e:
            self.logger.error(f"Erro ao parar TTS: {e}")

    def is_audio_available(self) -> bool:
        return self.use_audio and (self.has_ffplay or self.has_pygame or self.pyttsx3_engine)

    def __del__(self):
        """Destrutor para limpeza."""
        self.stop_tts()