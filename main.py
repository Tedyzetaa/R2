#!/usr/bin/env python3
import os
import sys
import subprocess
import asyncio
import platform
import logging
import requests
from datetime import datetime

# =============================================================================
# 1. PROTOCOLO DE AUTO-INSTALAÇÃO
# =============================================================================
def check_dependencies():
    deps = [
        "psutil", "python-dotenv", "requests", "diffusers", 
        "transformers", "accelerate", "peft", "torch", "torchvision",
        "llama-cpp-python", "geopy", "matplotlib", "cryptography"
    ]
    for dep in deps:
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--user", "--quiet"])

check_dependencies()

# =============================================================================
# 2. CONFIGURAÇÃO DE AMBIENTE E PATHS
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] R2_CORE: %(message)s')

# =============================================================================
# 3. VERIFICAÇÃO E DOWNLOAD DO DOLPHIN
# Garante que o arquivo baixado tenha o mesmo nome que o modelo usado localmente
# =============================================================================
def bootstrap_models():
    models_dir = os.path.join(BASE_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)

    # URL exata que você solicitou
    dolphin_path = os.path.join(models_dir, "dolphin-2.9-llama3-8b-Q4_K_M.gguf") # Nome do arquivo para salvar (Mantenha o mesmo que o Cérebro procura)
    dolphin_url = "https://huggingface.co/mradermacher/dolphin-2.9-llama3-8b-GGUF/resolve/main/dolphin-2.9-llama3-8b.Q4_K_M.gguf" # URL corrigida (Note o ponto antes do Q4_K_M)

    if not os.path.exists(dolphin_path):
        print("📥 [SISTEMA]: Baixando matriz neural Dolphin (Uncensored)...")


        try:
            with requests.get(dolphin_url, stream=True) as r:
                r.raise_for_status()
                with open(dolphin_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print("✅ [SISTEMA]: Dolphin acoplado com sucesso.")
        except Exception as e:
            print(f"❌ [ERRO]: Falha no download do Dolphin: {e}")

bootstrap_models()

# =============================================================================
# 4. GESTÃO DE TOKEN
# =============================================================================
if len(sys.argv) < 2:
    from dotenv import load_dotenv
    load_dotenv()
    TOKEN_ARG = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN_ARG:
        print("❌ [ERRO CRÍTICO]: TOKEN DE ACESSO NÃO DETECTADO.")
        sys.exit(1)
else:
    TOKEN_ARG = sys.argv[1]

os.environ["TELEGRAM_TOKEN"] = TOKEN_ARG

# =============================================================================
# 5. CARREGADOR DINÂMICO
# =============================================================================
MODULOS_STATUS = {}

def safe_import(friendly_name, path, class_name=None):
    try:
        module = __import__(path, fromlist=[class_name] if class_name else [])
        MODULOS_STATUS[friendly_name] = "✅ ONLINE"
        return getattr(module, class_name) if class_name else module
    except Exception as e:
        MODULOS_STATUS[friendly_name] = f"❌ OFFLINE ({type(e).__name__}: {e})"
        return None

SystemMonitor = safe_import("Monitor", "features.system_monitor", "SystemMonitor")
SystemScanner = safe_import("Scanner", "features.system_scanner", "SystemScanner")
TelegramBotUplink = safe_import("Uplink", "features.telegram_uplink", "TelegramBotUplink")
WeatherSystem = safe_import("Clima", "features.weather_system", "WeatherSystem")
AirTrafficControl = safe_import("Radar", "features.air_traffic", "AirTrafficControl")
FrontlineIntel = safe_import("Intel_War", "features.liveuamap_intel", "FrontlineIntel")
AstroDefense = safe_import("Astro", "features.astro_defense", "AstroDefenseSystem")
VolcanoMonitor = safe_import("Magma", "features.volcano_monitor", "VolcanoMonitor")
MarketSystem = safe_import("Mercado", "features.market_system", "MarketSystem")
LocalLlamaBrain = safe_import("Cérebro_Dolphin", "features.local_brain", "LocalLlamaBrain")
ImageGenerator = safe_import("Geração_Imagem", "features.image_gen", "ImageGenerator")

# =============================================================================
# 6. R2 CORE
# =============================================================================
class R2Core:
    def __init__(self, token):        
        self.token = token
        self.running = True
        self.start_time = datetime.now()
        self.update_queue = None # Será preenchido pelo Uplink
        
        # Módulos Base
        self.scanner = SystemScanner() if SystemScanner else None
        self.monitor = SystemMonitor(self) if SystemMonitor else None        
        self.weather_ops = WeatherSystem(api_key="SUA_CHAVE") if WeatherSystem else None
        self.radar_ops = AirTrafficControl() if AirTrafficControl else None
        self.intel_ops = FrontlineIntel() if FrontlineIntel else None
        self.astro_ops = AstroDefense() if AstroDefense else None
        self.volcano_ops = VolcanoMonitor() if VolcanoMonitor else None
        self.market_ops = MarketSystem() if MarketSystem else None
        self.visual_engine = ImageGenerator() if ImageGenerator else None #alterado para compatibilidade - não remover

        # Cérebro Neural (Dolphin) - Corrigido: sem o kwarg model_path
        self.brain = None
        if LocalLlamaBrain:
            print("🧠 [BRAIN]: Conectando sinapses do motor Dolphin (Unfiltered)...")
            try:
                self.brain = LocalLlamaBrain()
                # Dica: Certifique-se que o seu local_brain.py procura pelo arquivo gguf correto na pasta models
            except Exception as e:
                logging.error(f"Falha ao instanciar LLM local: {e}")
                MODULOS_STATUS["Cérebro_Dolphin"] = "⚠️ ERRO DE CARGA"        

        # Uplink Telegram
        self.uplink = None
        if TelegramBotUplink:
            try:
                self.uplink = TelegramBotUplink(self)
            except Exception as e:
                logging.critical(f"Falha ao instanciar Uplink: {e}")

    async def boot_sequence(self):
        print("\n" + "═"*70)
        print(f"🤖 R2 ASSISTANT CORE - PROTOCOLO INTEGRAL")
        print("═"*70)

        print("\n📊 [DIAGNÓSTICO DE SUBSISTEMAS]:")
        for mod, status in MODULOS_STATUS.items():
            print(f"  > {mod.ljust(20)} : {status}")
        print("-" * 70)

        try:
            if self.uplink:
                print("\n📡 [UPLINK]: Estabelecendo ponte segura com o Telegram...")
                if hasattr(self.uplink, 'iniciar_sistema'):
                    self.uplink.iniciar_sistema()
                
                print("🟢 [STATUS]: R2 totalmente operacional. Aguardando input.")
                while self.running:
                    await asyncio.sleep(3600)
        except Exception as e:
            logging.critical(f"Falha no Core Loop: {e}")

def main():
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    r2 = R2Core(TOKEN_ARG)
    try:
        asyncio.run(r2.boot_sequence())
    except KeyboardInterrupt:
        print("\n🛑 [SHUTDOWN]: Desligando...")

if __name__ == "__main__":
    main()
