import logging
import time
from core.audio_processor import AudioProcessor

logging.basicConfig(level=logging.INFO)

def test_audio():
    print("🔊 Testando sistema de áudio...")
    
    audio_processor = AudioProcessor()
    
    print("1. Testando sem voz (apenas texto)...")
    audio_processor.text_to_speech("Olá, este é um teste de voz do R2")
    
    # Aguarda um pouco para o áudio terminar
    time.sleep(3)
    
    print("2. Testando segunda mensagem...")
    audio_processor.text_to_speech("Sistema de voz funcionando corretamente")
    
    time.sleep(3)
    print("✅ Teste de áudio concluído")

if __name__ == "__main__":
    test_audio()