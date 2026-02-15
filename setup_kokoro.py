import os
import urllib.request
import sys
from colorama import Fore, init

init(autoreset=True)

def download_file(url, filename):
    print(Fore.CYAN + f"⬇️ Baixando {filename}...")
    try:
        urllib.request.urlretrieve(url, filename)
        print(Fore.GREEN + f"✅ {filename} baixado com sucesso!")
    except Exception as e:
        print(Fore.RED + f"❌ Erro ao baixar {filename}: {e}")
        sys.exit(1)

def main():
    # Cria pasta de modelos se não existir
    if not os.path.exists("models"):
        os.makedirs("models")

    # URLs oficiais do projeto Kokoro-82M (Versão ONNX)
    base_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/"
    
    # 1. O Modelo Neural (82MB)
    model_path = os.path.join("models", "kokoro-v0_19.onnx")
    if not os.path.exists(model_path):
        download_file(f"{base_url}kokoro-v0_19.onnx", model_path)
    else:
        print(Fore.YELLOW + "⚡ Modelo Kokoro já existe.")

    # 2. O Mapeamento de Vozes
    voices_path = os.path.join("models", "voices.json")
    if not os.path.exists(voices_path):
        download_file(f"{base_url}voices.json", voices_path)
    else:
        print(Fore.YELLOW + "⚡ Arquivo de vozes já existe.")

    print(Fore.GREEN + "\n🚀 SETUP KOKORO CONCLUÍDO. O R2 JÁ PODE FALAR.")

if __name__ == "__main__":
    main()