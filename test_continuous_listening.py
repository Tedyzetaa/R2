import time
import logging
from core.voice_engine import VoiceEngine

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def voice_callback(text):
    print(f"🎯 COMANDO RECEBIDO: '{text}'")
    # Simular processamento
    print("🔄 Processando comando...")
    time.sleep(2)  # Simula tempo de processamento
    print("✅ Comando processado, continuando escuta...")

def test_continuous_listening():
    print("🎧 TESTE DE ESCUTA CONTÍNUA")
    print("Fale comandos como 'olá', 'hora', 'ajuda'")
    print("Pressione Ctrl+C para parar\n")
    
    engine = VoiceEngine()
    
    if not engine.is_audio_available():
        print("❌ Microfone não disponível")
        return
    
    try:
        engine.start_listening(voice_callback)
        print("✅ Escuta iniciada. Falando comandos...")
        
        # Manter o teste rodando
        while True:
            time.sleep(1)
            if not engine.get_listening_status():
                print("❌ Escuta parou inesperadamente!")
                break
                
    except KeyboardInterrupt:
        print("\n⏹️ Parando teste...")
    finally:
        engine.stop_listening()
        print("✅ Teste finalizado")

if __name__ == "__main__":
    test_continuous_listening()