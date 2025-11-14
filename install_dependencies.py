#!/usr/bin/env python3
"""
Script para instalar dependências do R2 Assistant
"""

import subprocess
import sys

def install_requirements():
    """Instala as dependências do projeto"""
    
    requirements = [
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "SpeechRecognition==3.10.0", 
        "gTTS==2.3.2",
        "pygame==2.5.2",
        "matplotlib==3.7.2",
        "pandas==2.0.3",
        "numpy==1.24.3",
        "mplfinance==0.12.10",
        "Pillow==10.0.1",
        "python-binance==1.0.19",
        "pyautogui==0.9.54",
        "pyperclip==1.8.2"
    ]
    
    print("🚀 Instalando dependências do R2 Assistant...")
    
    for package in requirements:
        try:
            print(f"📦 Instalando {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} instalado com sucesso!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar {package}: {e}")
    
    print("\n🎉 Todas as dependências foram instaladas!")
    print("\n📝 Próximos passos:")
    print("1. Configure suas chaves API no arquivo .env")
    print("2. Execute: python main.py")
    print("3. Use 'R2, ativar trading automático' para iniciar!")

if __name__ == "__main__":
    install_requirements()