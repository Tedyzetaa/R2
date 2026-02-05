import os
import pygame
import asyncio
import edge_tts
import pyttsx3
import threading

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

AUDIO_FILE = "fala_r2.mp3"

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

def falar(texto):
    if not texto: return

    def _thread_voz():
        try:
            # Tenta Online
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_gerar_audio_online(texto))
            loop.close()
            _tocar_audio_online()
        except:
            # Falhou? Usa o Offline sem reclamar no terminal
            falar_offline(texto)

    threading.Thread(target=_thread_voz, daemon=True).start()

if __name__ == "__main__":
    falar("Módulo de voz R2 operacional.")
