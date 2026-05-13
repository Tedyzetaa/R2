import os
import pygame
import asyncio
import edge_tts
import pyttsx3
import threading
import re # [FIXED: batalha-1.2]
from jarvis_rvc import sintetizar_jarvis

# 1. TENTA INICIAR O MIXER DE AUDIO (ONLINE)
try:
    pygame.mixer.init()
except:
    pass

# 2. TENTA INICIAR O MOTOR OFFLINE (ROBÔ)
try:
    engine_offline = pyttsx3.init()
    voices = engine_offline.getProperty('voices')
    # Tenta pegar voz em PT-BR
    for v in voices:
        if "brazil" in v.id.lower() or "portuguese" in v.name.lower():
            engine_offline.setProperty('voice', v.id)
            break
    engine_offline.setProperty('rate', 190) 
except:
    engine_offline = None

# [FIXED: batalha-1.1]
AUDIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fala_r2.mp3")

def limpar_para_fala(texto: str) -> str: # [FIXED: batalha-1.2]
    """Remove markdown e símbolos antes da síntese de voz."""
    # Substitui blocos de código por aviso falado
    texto = re.sub(r'```[\s\S]*?```', 'bloco de código omitido.', texto)
    # Remove símbolos de formatação inline
    texto = re.sub(r'[*_`#~>]', '', texto)
    # Colapsa espaços múltiplos
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

async def _gerar_audio_online(texto):
    """Gera o arquivo de áudio usando a Microsoft"""
    communicate = edge_tts.Communicate(texto, "pt-BR-AntonioNeural")
    await communicate.save(AUDIO_FILE)

def _tocar_audio_online():
    if os.path.exists(AUDIO_FILE):
        try:
            pygame.mixer.music.load(AUDIO_FILE)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"❌ Erro player: {e}")

def falar_offline(texto):
    """Fallback para voz robótica"""
    if engine_offline:
        try:
            engine_offline.say(texto)
            engine_offline.runAndWait()
        except:
            pass

def falar(texto, on_start=None, on_end=None): # [FIXED: batalha-1.3]
    """
    Sintetiza e toca o texto em voz alta.
    on_start: callable chamado imediatamente antes de tocar o áudio.
    on_end:   callable chamado imediatamente após o áudio terminar.
    """
    if not texto:
        return
    texto = limpar_para_fala(texto) # [FIXED: batalha-1.2]

    def _thread_voz():
        try:
            # Tenta online (Microsoft Neural)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_gerar_audio_online(texto))
            loop.close()
            if on_start: # [FIXED: batalha-1.3]
                on_start()
            _tocar_audio_online()
            if on_end: # [FIXED: batalha-1.3]
                on_end()
        except Exception:
            # Fallback offline (pyttsx3)
            if on_start: # [FIXED: batalha-1.3]
                on_start()
            falar_offline(texto)
            if on_end: # [FIXED: batalha-1.3]
                on_end()

    threading.Thread(target=_thread_voz, daemon=True).start()

# Adicione no topo do voz.py (junto aos outros imports)

def falar_jarvis(texto, on_start, on_end, loop):
    async def _processo():
        try:
            if on_start: await on_start()
            
            # Chama o Jarvis RVC (seu jarvis_rvc.py)
            from jarvis_rvc import sintetizar_jarvis
            audio_url = await sintetizar_jarvis(texto)
            
            # Aqui você envia o comando para o Frontend tocar o áudio
            # (Exemplo via retorno do WebSocket que você já tem no main2.py)
            
        except Exception as e:
            print(f"Falha no Jarvis, usando fallback: {e}")
            await falar(texto) # Seu fallback para Edge TTS
        finally:
            if on_end: await on_end()

    asyncio.run_coroutine_threadsafe(_processo(), loop)