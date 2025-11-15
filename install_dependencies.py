#!/usr/bin/env python3
"""
Script de instalação das dependências do R2 Assistant
"""

import os
import sys
import subprocess
import platform

def install_requirements():
    """Instala todas as dependências necessárias."""
    
    requirements = [
        "vosk",
        "pyaudio",
        "speechrecognition",
        "gtts",
        "pygame",
        "requests",
        "python-dotenv",
        "pyautogui",
        "pyperclip",
        "tkinter"
    ]
    
    print("🚀 Instalando dependências do R2 Assistant...")
    
    for package in requirements:
        try:
            print(f"📦 Instalando {package}...")
            if package == "pyaudio":
                # PyAudio pode precisar de tratamento especial no Windows
                if platform.system() == "Windows":
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyaudio"])
                else:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyaudio"])
            elif package == "tkinter":
                # Tkinter geralmente vem com Python
                print("✅ Tkinter geralmente já está instalado com Python")
            else:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                
            print(f"✅ {package} instalado com sucesso")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar {package}: {e}")
            
    print("\n📥 Baixando modelo de voz Vosk...")
    download_vosk_model()

def download_vosk_model():
    """Baixa o modelo de voz Vosk em português."""
    import urllib.request
    import zipfile
    
    model_url = "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"
    model_dir = "./model"
    zip_path = os.path.join(model_dir, "vosk-model-small-pt-0.3.zip")
    
    os.makedirs(model_dir, exist_ok=True)
    
    try:
        print("📥 Baixando modelo Vosk em português...")
        urllib.request.urlretrieve(model_url, zip_path)
        
        print("📦 Extraindo modelo...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(model_dir)
            
        print("✅ Modelo Vosk instalado com sucesso")
        
        # Remove o arquivo zip
        os.remove(zip_path)
        
    except Exception as e:
        print(f"❌ Erro ao baixar modelo Vosk: {e}")
        print("💡 Você pode baixar manualmente em:")
        print("https://alphacephei.com/vosk/models")
        print("E extrair em ./model/vosk-model-small-pt-0.3/")

if __name__ == "__main__":
    install_requirements()