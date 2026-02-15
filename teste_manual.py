import os
import json
import sounddevice as sd
from kokoro_onnx import Kokoro
from colorama import Fore, init

init(autoreset=True)

MODEL = "models/kokoro-v1.0.onnx"
VOICES = "models/voices-v1.0.json" # O arquivo que você colocou manualmente

print(f"🔍 Verificando arquivo manual: {VOICES}")

if not os.path.exists(VOICES):
    print(Fore.RED + "❌ Arquivo não encontrado! Você copiou para a pasta 'models' e renomeou?")
    exit()

try:
    with open(VOICES, 'r', encoding='utf-8') as f:
        dados = json.load(f)
        # Verifica se tem a voz do Papai Noel Tático (pm_santa)
        if "pm_santa" in dados:
            print(Fore.GREEN + "✅ Arquivo VÁLIDO! Vozes Brasileiras detectadas.")
        else:
            print(Fore.YELLOW + "⚠️ Arquivo abre, mas não achei 'pm_santa'. Pode ser uma versão antiga.")
except Exception as e:
    print(Fore.RED + f"❌ O arquivo está corrompido (Provavelmente salvou um HTML de erro). Baixe de novo!\nErro: {e}")
    exit()

print(Fore.CYAN + "🔊 Tentando falar...")
kokoro = Kokoro(MODEL, VOICES)
samples, rate = kokoro.create(
    "Protocolo manual aceito. Voz brasileira ativa.", 
    voice="pm_santa", 
    speed=1.0, 
    lang="pt-br"
)
sd.play(samples, rate)
sd.wait()
print(Fore.GREEN + "🚀 SUCESSO! O R2 ESTÁ FALANDO.")