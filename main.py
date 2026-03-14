import sys
import os
import asyncio
import platform
import subprocess
import threading
import time
import logging
from datetime import datetime

# --- 1. PROTOCOLO DE AUTO-INSTALAÇÃO (RESILIÊNCIA CRÍTICA) ---
def check_dependencies():
    """Verifica e instala bibliotecas ausentes antes de iniciar o Core"""
    deps = ["psutil", "python-dotenv", "requests", "feedparser", "telegrams", "matplotlib"]
    for dep in deps:
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            print(f"📦 [SISTEMA]: Instalando dependência ausente: {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--user"])

check_dependencies()

# --- 2. CONFIGURAÇÃO DE AMBIENTE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# --- 3. GESTÃO DE TOKEN E ARGUMENTOS ---
if len(sys.argv) < 2:
    from dotenv import load_dotenv
    load_dotenv()
    TOKEN_ARG = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN_ARG:
        print("❌ [ERRO]: Token ausente em sys.argv e .env. Abortando.")
        sys.exit(1)
else:
    TOKEN_ARG = sys.argv[1]

os.environ["TELEGRAM_TOKEN"] = TOKEN_ARG

# --- 5. VERIFICADOR DE MODELOS DE IA ---
def verify_ai_models():
    """Verifica e baixa os modelos de IA necessários (SD e LoRA)"""
    models_dir = os.path.join(BASE_DIR, "models", "checkpoints")
    loras_dir = os.path.join(BASE_DIR, "models", "loras")
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(loras_dir, exist_ok=True)

    # Configuração dos alvos
    targets = {
        "SD_1.5_Base": {
            "path": os.path.join(models_dir, "v1-5-pruned.safetensors"),
            "url": "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned.safetensors"
        },
        "Detailed_Perfection_LoRA": {
            "path": os.path.join(loras_dir, "detailed_perfection.safetensors"),
            "url": "https://civitai.com/api/download/models/461125" # Link direto da API do CivitAI
        }
    }

    for name, info in targets.items():
        if not os.path.exists(info["path"]):
            print(f"📥 [SISTEMA]: Modelo {name} não encontrado. Iniciando download...")
            try:
                import requests
                response = requests.get(info["url"], stream=True)
                with open(info["path"], "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"✅ [SISTEMA]: {name} baixado com sucesso.")
            except Exception as e:
                print(f"❌ [ERRO]: Falha ao baixar {name}: {e}")

# Executa a verificação antes de carregar o restante do sistema
verify_ai_models()

# --- 4. CARREGADOR DINÂMICO DE MÓDULOS COM FAILSAFE ---
MODULOS_STATUS = {}

def safe_import(friendly_name, path, class_name=None):
    try:
        module = __import__(path, fromlist=[class_name] if class_name else [])
        MODULOS_STATUS[friendly_name] = "✅ ONLINE"
        return getattr(module, class_name) if class_name else module
    except Exception as e:
        MODULOS_STATUS[friendly_name] = f"❌ OFFLINE ({type(e).__name__})"
        return None

# Importação de Features
SystemMonitor = safe_import("Monitor", "features.system_monitor", "SystemMonitor")
SystemScanner = safe_import("Scanner", "features.system_scanner", "SystemScanner")
TelegramBotUplink = safe_import("Uplink", "features.telegram_uplink", "TelegramBotUplink")
WeatherSystem = safe_import("Clima", "features.weather_system", "WeatherSystem")
AirTrafficControl = safe_import("Radar", "features.air_traffic", "AirTrafficControl")
FrontlineIntel = safe_import("Intel", "features.liveuamap_intel", "FrontlineIntel")
QuantumCore = safe_import("Quantum", "quantum_module", "QuantumCoreManager")
LocalLlamaBrain = safe_import("Cérebro", "features.local_brain", "LocalLlamaBrain")

# --- 5. R2 CORE: O CÉREBRO INTEGRAL ---
class R2Core:
    def __init__(self, token):
        self.token = token
        self.running = True
        self.start_time = datetime.now()
        
        # Inicialização de Instâncias com Verificação de Redundância
        self.scanner = SystemScanner() if SystemScanner else None
        self.monitor = SystemMonitor(self) if SystemMonitor else None
        self.quantum = QuantumCore() if QuantumCore else None
        
        # Módulos Táticos
        self.weather_ops = WeatherSystem(api_key="SUA_KEY") if WeatherSystem else None
        self.radar_ops = AirTrafficControl() if AirTrafficControl else None
        self.intel_ops = FrontlineIntel() if FrontlineIntel else None
        
        # --- LÓGICA DO MODELO DE LINGUAGEM (LLM) ---
        self.brain = None
        if LocalLlamaBrain:
            print("🧠 [BRAIN]: Inicializando motor neural local...")
            try:
                self.brain = LocalLlamaBrain()
                MODULOS_STATUS["Cérebro"] = "✅ ONLINE (LLM Ativa)"
            except Exception as e:
                print(f"⚠️ [BRAIN]: Falha ao carregar LLM: {e}")
                MODULOS_STATUS["Cérebro"] = "⚠️ ERRO DE CARGA"

        # Uplink (Interface de Comunicação)
        self.uplink = None
        if TelegramBotUplink:
            try:
                self.uplink = TelegramBotUplink(self)
            except Exception as e:
                print(f"❌ [UPLINK]: Erro fatal: {e}")

    def get_uptime(self):
        delta = datetime.now() - self.start_time
        return str(delta).split(".")[0]

    async def self_healing_protocol(self):
        """Protocolo que monitora a saúde do sistema e tenta reconectar o Uplink"""
        while self.running:
            await asyncio.sleep(60)
            if self.uplink and not hasattr(self.uplink, 'app'):
                print("🔄 [HEALING]: Detectada queda no Uplink. Tentando reset...")
                # Lógica de reinicialização aqui se necessário

    async def boot_sequence(self):
        """Sequência de boot completa e detalhada"""
        print("\n" + "═"*60)
        print(f"🤖 R2 ASSISTANT CORE - PROTOCOLO INTEGRAL")
        print(f"📅 DATA: {self.start_time.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"📍 HOST: {platform.node()} ({platform.system()})")
        print("═"*60)

        # Status Report
        print("\n📊 [ESTADO DO HARDWARE/SOFTWARE]:")
        for mod, status in MODULOS_STATUS.items():
            print(f"  > {mod.ljust(10)} : {status}")

        # Inicia Watchdog
        asyncio.create_task(self.self_healing_protocol())

        try:
            if self.uplink:
                print("\n📡 [UPLINK]: Estabelecendo ponte com Telegram...")
                # Aqui o bot entra no loop infinito de polling ou webhook
                # O uplink deve ser assíncrono para não travar o loop do core
                while self.running:
                    await asyncio.sleep(10)
            else:
                print("\n⚠️ [AVISO]: Sistema operando em modo diagnóstico (Sem Uplink).")
                while self.running: await asyncio.sleep(3600)
                
        except Exception as e:
            print(f"💥 [ERRO]: Falha na execução do Core: {e}")

# --- 6. PONTO DE ENTRADA ---
def main():
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    r2 = R2Core(TOKEN_ARG)

    try:
        asyncio.run(r2.boot_sequence())
    except KeyboardInterrupt:
        print("\n🛑 [SHUTDOWN]: Desligando protocolos com segurança.")
        r2.running = False
    except Exception as e:
        print(f"💀 [CRASH]: Sistema encerrado abruptamente: {e}")

if __name__ == "__main__":
    main()
