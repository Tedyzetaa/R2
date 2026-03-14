#!/usr/bin/env python3
import os
import sys
import subprocess
import asyncio
import platform
import logging
from datetime import datetime

# =============================================================================
# 1. PROTOCOLO DE AUTO-INSTALAÇÃO (RESILIÊNCIA CRÍTICA)
# =============================================================================
def check_dependencies():
    """Verifica e instala bibliotecas ausentes antes de iniciar o Core"""
    deps = [
        "psutil", "python-dotenv", "requests", "diffusers", 
        "transformers", "accelerate", "peft", "torch", "torchvision",
        "llama-cpp-python", "geopy", "matplotlib", "cryptography"
    ]
    print("📦 [SISTEMA]: Verificando integridade das dependências...")
    for dep in deps:
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            print(f"📦 [SISTEMA]: Instalando dependência crítica: {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--user", "--quiet"])

check_dependencies()
import requests  # Seguro importar agora

# =============================================================================
# 2. CONFIGURAÇÃO DE AMBIENTE E PATHS
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] R2_CORE: %(message)s',
    handlers=[logging.FileHandler("r2_system.log"), logging.StreamHandler()]
)

# =============================================================================
# 3. VERIFICAÇÃO E DOWNLOAD DE MODELOS (DOLPHIN & LORA)
# =============================================================================
def bootstrap_models():
    """Garante que o Dolphin e o LoRA de Perfeição existam na máquina"""
    models_dir = os.path.join(BASE_DIR, "models")
    loras_dir = os.path.join(models_dir, "loras")
    
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(loras_dir, exist_ok=True)

    targets = {
        "Dolphin_Brain_Uncensored": {
            "path": os.path.join(models_dir, "dolphin-2.9-llama3-8b-q4_k_m.gguf"),
            "url": "https://huggingface.co/bartowski/dolphin-2.9-llama3-8b-GGUF/resolve/main/dolphin-2.9-llama3-8b-Q4_K_M.gguf"
        },
        "Detailed_Perfection_LoRA": {
            "path": os.path.join(loras_dir, "detailed_perfection.safetensors"),
            # Link da API do CivitAI baseado no ID fornecido
            "url": "https://civitai.com/api/download/models/411088" 
        }
    }

    for name, info in targets.items():
        if not os.path.exists(info["path"]):
            print(f"📥 [SISTEMA]: Baixando matriz neural {name}... (Isso pode demorar)")
            try:
                with requests.get(info["url"], stream=True) as r:
                    r.raise_for_status()
                    with open(info["path"], 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                print(f"✅ [SISTEMA]: {name} acoplado com sucesso.")
            except Exception as e:
                print(f"❌ [ERRO]: Falha no download de {name}: {e}")

bootstrap_models()

# =============================================================================
# 4. GESTÃO DE TOKEN E ARGUMENTOS
# =============================================================================
if len(sys.argv) < 2:
    from dotenv import load_dotenv
    load_dotenv()
    TOKEN_ARG = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN_ARG:
        print("\n" + "!"*60)
        print("❌ [ERRO CRÍTICO]: TOKEN DE ACESSO NÃO DETECTADO.")
        print("MODO DE USO: !python main.py SEU_TOKEN_AQUI")
        print("!"*60 + "\n")
        sys.exit(1)
else:
    TOKEN_ARG = sys.argv[1]

os.environ["TELEGRAM_TOKEN"] = TOKEN_ARG

# =============================================================================
# 5. CARREGADOR DINÂMICO DE MÓDULOS COM FAILSAFE
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

# Importação de toda a suíte de Features do R2
SystemMonitor = safe_import("Monitor", "features.system_monitor", "SystemMonitor")
SystemScanner = safe_import("Scanner", "features.system_scanner", "SystemScanner")
TelegramBotUplink = safe_import("Uplink", "features.telegram_uplink", "TelegramBotUplink")
WeatherSystem = safe_import("Clima", "features.weather_system", "WeatherSystem")
AirTrafficControl = safe_import("Radar", "features.air_traffic", "AirTrafficControl")
FrontlineIntel = safe_import("Intel_War", "features.liveuamap_intel", "FrontlineIntel")
AstroDefense = safe_import("Astro", "features.astro_defense", "AstroDefenseSystem")
VolcanoMonitor = safe_import("Magma", "features.volcano_monitor", "VolcanoMonitor")
MarketSystem = safe_import("Mercado", "features.market_system", "MarketSystem")
QuantumCore = safe_import("Quantum_Trade", "quantum_module", "QuantumCoreManager")
LocalLlamaBrain = safe_import("Cérebro_Dolphin", "features.local_brain", "LocalLlamaBrain")
ImageGenerator = safe_import("Geração_Imagem", "features.image_gen", "ImageGenerator")

# =============================================================================
# 6. R2 CORE: O CÉREBRO INTEGRAL
# =============================================================================
class R2Core:
    def __init__(self, token):
        self.token = token
        self.running = True
        self.start_time = datetime.now()
        
        # Subsistemas de Hardware
        self.scanner = SystemScanner() if SystemScanner else None
        self.monitor = SystemMonitor(self) if SystemMonitor else None
        self.quantum = QuantumCore() if QuantumCore else None
        
        # Sensores Táticos
        self.weather_ops = WeatherSystem(api_key="8db4b830d939639535698f1211e0e980") if WeatherSystem else None
        self.radar_ops = AirTrafficControl() if AirTrafficControl else None
        self.intel_ops = FrontlineIntel() if FrontlineIntel else None
        self.astro_ops = AstroDefense() if AstroDefense else None
        self.volcano_ops = VolcanoMonitor() if VolcanoMonitor else None
        self.market_ops = MarketSystem() if MarketSystem else None
        
        # Módulo Visual (Imagem com LoRA)
        self.visual_engine = ImageGenerator() if ImageGenerator else None
        
        # Cérebro Neural (Dolphin)
        self.brain = None
        if LocalLlamaBrain:
            print("🧠 [BRAIN]: Conectando sinapses do motor Dolphin (Unfiltered)...")
            try:
                self.brain = LocalLlamaBrain(model_path="models/dolphin-2.9-llama3-8b-q4_k_m.gguf")
            except Exception as e:
                logging.error(f"Falha ao carregar LLM: {e}")
                MODULOS_STATUS["Cérebro_Dolphin"] = "⚠️ ERRO DE CARGA"

        # Interface de Comunicação
        self.uplink = None
        if TelegramBotUplink:
            try:
                self.uplink = TelegramBotUplink(self)
            except Exception as e:
                logging.critical(f"Falha ao instanciar Uplink: {e}")

    def get_uptime(self):
        delta = datetime.now() - self.start_time
        return str(delta).split(".")[0]

    async def self_healing_protocol(self):
        """Monitora a integridade do sistema em background"""
        while self.running:
            await asyncio.sleep(60)
            if self.scanner:
                stats = self.scanner.get_stats()
                if stats.get('cpu', 0) > 95:
                    logging.warning("⚠️ ALERTA DE RECURSOS: CPU em carga crítica.")

    async def boot_sequence(self):
        """Sequência de inicialização completa do R2"""
        print("\n" + "═"*70)
        print(f"🤖 R2 ASSISTANT CORE - PROTOCOLO INTEGRAL ATIVADO")
        print(f"📅 DATA/HORA: {self.start_time.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"📍 HOST/NÓ: {platform.node()} ({platform.system()})")
        print("═"*70)

        # Relatório de Diagnóstico de Módulos
        print("\n📊 [DIAGNÓSTICO DE SUBSISTEMAS]:")
        for mod, status in MODULOS_STATUS.items():
            print(f"  > {mod.ljust(20)} : {status}")
        print("-" * 70)

        # Ativa o Watchdog
        asyncio.create_task(self.self_healing_protocol())

        try:
            if self.uplink:
                print("\n📡 [UPLINK]: Estabelecendo ponte segura com o Telegram...")
                # Lógica para manter o processo ativo. O uplink geralmente gerencia seu próprio loop
                # através da biblioteca do telegram, mas mantemos o core vivo aqui.
                if hasattr(self.uplink, 'iniciar_sistema'):
                    self.uplink.iniciar_sistema()
                
                print("🟢 [STATUS]: R2 totalmente operacional. Aguardando input.")
                while self.running:
                    await asyncio.sleep(3600)
            else:
                print("\n⚠️ [AVISO]: Uplink ausente. Sistema operando em modo local/diagnóstico.")
                while self.running: 
                    await asyncio.sleep(3600)
                
        except Exception as e:
            logging.critical(f"Falha catastrófica no Core Loop: {e}")

# =============================================================================
# 7. EXECUÇÃO PRINCIPAL
# =============================================================================
def main():
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    r2 = R2Core(TOKEN_ARG)

    try:
        asyncio.run(r2.boot_sequence())
    except KeyboardInterrupt:
        print("\n🛑 [SHUTDOWN]: Sequência de encerramento iniciada pelo Operador. Desligando...")
        r2.running = False
    except Exception as e:
        with open("emergency_crash.log", "a") as f:
            f.write(f"[{datetime.now()}] CRASH: {str(e)}\n")
        print(f"💀 [CRASH]: Sistema colapsou. Detalhes em emergency_crash.log")

if __name__ == "__main__":
    main()
