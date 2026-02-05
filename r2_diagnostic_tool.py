import os
import sys
import importlib
import threading
import time
from colorama import Fore, Style, init

init(autoreset=True)

class R2Diagnostic:
    def __init__(self):
        self.modules = {
            "Cérebro (Llama)": "features.local_brain",
            "Voz (Offline/Online)": "voz",
            "Radar Aéreo": "features.air_traffic",
            "Intel de Guerra": "features.intel_war",
            "Clima": "features.weather_system",
            "Sentinela (Webcam)": "features.sentinel_system",
            "Uplink Telegram": "features.telegram_uplink",
            "Monitor Solar (NOAA)": "features.noaa.noaa_service",
            "Scanner de Rede": "features.network_scanner",
            "Speedtest": "features.net_speed"
        }

    def run_full_test(self):
        print(Fore.CYAN + "\n" + "="*50)
        print(Fore.CYAN + "🧪 R2 ASSISTANT - DIAGNÓSTICO DE SISTEMAS")
        print(Fore.CYAN + "="*50 + "\n")

        for name, path in self.modules.items():
            status = Fore.YELLOW + "⌛ TESTANDO..."
            print(f"{name:<25} {status}", end="\r")
            
            try:
                # Tenta importar o módulo dinamicamente
                mod = importlib.import_module(path)
                print(f"{name:<25} {Fore.GREEN}✅ OPERACIONAL")
            except Exception as e:
                print(f"{name:<25} {Fore.RED}❌ FALHA: {str(e)[:50]}")

        print(Fore.CYAN + "\n" + "="*50)

    def search_new_features(self):
        """Lista arquivos na pasta features que ainda não estão no índice principal"""
        print(Fore.YELLOW + "\n🔍 EXPLORANDO NOVAS CAPACIDADES (Pasta /features)...")
        features_path = os.path.join(os.getcwd(), "features")
        
        if not os.path.exists(features_path):
            print(Fore.RED + "❌ Pasta 'features' não encontrada.")
            return

        found = []
        for root, dirs, files in os.walk(features_path):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    rel_path = os.path.relpath(os.path.join(root, file), os.getcwd())
                    found.append(rel_path)

        if found:
            print(Fore.GREEN + f"✨ Encontrados {len(found)} módulos/scripts disponíveis:")
            for f in found:
                print(f"  [+] {f}")
        else:
            print(Fore.WHITE + "ℹ️ Nenhum módulo adicional encontrado.")

    def menu(self):
        while True:
            print(Fore.WHITE + "\n[1] Diagnóstico Completo")
            print(Fore.WHITE + "[2] Pesquisar Módulos no Disco")
            print(Fore.WHITE + "[3] Sair")
            
            choice = input(Fore.CYAN + "\nComando > ")
            
            if choice == "1":
                self.run_full_test()
            elif choice == "2":
                self.search_new_features()
            elif choice == "3":
                break
            else:
                print(Fore.RED + "Opção Inválida.")

if __name__ == "__main__":
    diag = R2Diagnostic()
    diag.menu()