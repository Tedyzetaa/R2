import speech_recognition as sr
import threading
import time

class EarSystem:
    def __init__(self, wake_word="r2"):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.wake_word = wake_word.lower()
        self.is_active = False 
        
        # Configurações iniciais de sensibilidade
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

    def listen_active(self, callback):
        """Modo Sentinela: Escuta passiva leve"""
        def loop():
            print("🎤 [EAR]: Sentinela auditivo iniciado.")
            with self.microphone as source:
                # Calibragem inicial rápida
                self.recognizer.adjust_for_ambient_noise(source, duration=1)

            while True:
                if not self.is_active:
                    try:
                        with self.microphone as source:
                            # Escuta rápida (buffer curto)
                            audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=2)
                            text = self.recognizer.recognize_google(audio, language="pt-BR").lower()
                            
                            if self.wake_word in text:
                                self.is_active = True
                                callback() # Chama a GUI
                    except (sr.WaitTimeoutError, sr.UnknownValueError):
                        continue # Ignora silêncio ou barulho irrelevante
                    except Exception as e:
                        print(f"⚠️ Erro no loop passivo: {e}")
                        time.sleep(1)
                else:
                    time.sleep(0.5)

        threading.Thread(target=loop, daemon=True).start()

    def capture_full_command(self):
        """Modo Focado: Escuta o comando completo com alta precisão"""
        # Ajustes para ignorar a própria voz do bot e respiração
        self.recognizer.pause_threshold = 1.5  # Espera 1.5s de silêncio antes de finalizar
        self.recognizer.phrase_threshold = 0.3 # Ignora barulhos muito curtos (<0.3s)
        
        with self.microphone as source:
            try:
                # Recalibragem relâmpago para o momento atual (ex: ar condicionado ligou)
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                print("🎤 [EAR]: Aguardando comando tático...")
                # Timeout: Espera 5s você COMEÇAR a falar
                # Phrase Limit: Te dá 10s para FALAR a frase toda
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                text = self.recognizer.recognize_google(audio, language="pt-BR")
                self.is_active = False
                return text
            except sr.WaitTimeoutError:
                print("❌ Timeout: Operador não falou nada.")
                self.is_active = False
                return None
            except sr.UnknownValueError:
                print("❌ Erro: Não entendi o áudio.")
                self.is_active = False
                return None
            except Exception as e:
                print(f"❌ Erro crítico na escuta: {e}")
                self.is_active = False
                return None