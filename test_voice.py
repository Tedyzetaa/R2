import speech_recognition as sr
import logging

logging.basicConfig(level=logging.INFO)

def test_microphone():
    r = sr.Recognizer()
    
    # Listar microfones disponíveis
    print("🎤 Microfones disponíveis:")
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"  {index}: {name}")
    
    try:
        with sr.Microphone() as source:
            print("🔊 Ajustando para ruído ambiente...")
            r.adjust_for_ambient_noise(source, duration=2)
            print("🎙️ Fale algo...")
            
            audio = r.listen(source, timeout=10)
            print("✅ Áudio capturado! Processando...")
            
            text = r.recognize_google(audio, language='pt-BR')
            print(f"📝 Você disse: {text}")
            
    except sr.WaitTimeoutError:
        print("❌ Tempo esgotado. Nenhum áudio detectado.")
    except sr.UnknownValueError:
        print("❌ Não foi possível entender o áudio.")
    except sr.RequestError as e:
        print(f"❌ Erro no serviço de reconhecimento: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    test_microphone()