#!/usr/bin/env python3
"""
Script para corrigir problemas de instalação
"""

import subprocess
import sys
import os

def fix_installation():
    print("🔧 Corrigindo problemas de instalação...")
    
    # 1. Corrigir numpy
    print("📦 Reinstalando numpy...")
    subprocess.call([sys.executable, "-m", "pip", "uninstall", "numpy", "-y"])
    subprocess.call([sys.executable, "-m", "pip", "install", "numpy==1.24.3"])
    
    # 2. Instalar mplfinance com versão correta
    print("📦 Instalando mplfinance...")
    subprocess.call([sys.executable, "-m", "pip", "install", "mplfinance==0.12.10b0"])
    
    # 3. Verificar se todos os módulos estão acessíveis
    print("🔍 Verificando imports...")
    
    modules_to_check = [
        "commands.basic_commands",
        "commands.system_commands", 
        "commands.web_commands",
        "commands.crypto_commands",
        "trading.binance_client",
        "trading.trading_engine"
    ]
    
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"✅ {module} - OK")
        except ImportError as e:
            print(f"❌ {module} - Erro: {e}")
    
    print("\n🎉 Correção concluída!")

if __name__ == "__main__":
    fix_installation()