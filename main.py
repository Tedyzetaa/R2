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
        "llama-cpp-python", "geopy", "matplotlib", "cryptography", "cloudscraper",
        "python-telegram-bot", "playwright"
    ]
    for dep in deps:
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--user", "--quiet"])

check_dependencies()
import site
import importlib
# Força o Python a recarregar os caminhos de bibliotecas instaladas agora
importlib.reload(site)

# =============================================================================
# 2. CONFIGURAÇÃO DE AMBIENTE E PATHS
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] CORE: %(message)s')

# =============================================================================
# 3. VERIFICAÇÃO E DOWNLOAD DO DOLPHIN
# =============================================================================
def bootstrap_models():
    models_dir = os.path.join(BASE_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)

    # URL exata que você solicitou
    dolphin_path = os.path.join(models_dir, "dolphin-2.9-llama3-8b-Q4_K_M.gguf") # Nome do arquivo para salvar (Mantenha o mesmo que o Cérebro procura)
    dolphin_url = "https://huggingface.co/mradermacher/dolphin-2.9-llama3-8b-GGUF/resolve/main/dolphin-2.9-llama3-8b.Q4_K_M.gguf"

    if not os.path.exists(dolphin_path):
        print("📥 Baixando matriz Dolphin (Uncensored)...")
        try:
            with requests.get(dolphin_url, stream=True) as r:
                r.raise_for_status()
                with open(dolphin_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print("✅ Dolphin acoplado.")
        except Exception as e:
            print(f"❌ Erro no download: {e}")

bootstrap_models()

# =============================================================================
# 4. GESTÃO DE TOKEN
# =============================================================================
if len(sys.argv) < 2:
    from dotenv import load_dotenv
    load_dotenv()
    TOKEN_ARG = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN_ARG:
        sys.exit(1)
else:
    TOKEN_ARG = sys.argv[1]

os.environ["TELEGRAM_TOKEN"] = TOKEN_ARG

# =============================================================================
# 5. CARREGADOR DINÂMICO
# =============================================================================
MODULOS_STATUS = {}
# Funções de importação segura (Não mexer)
def safe_import(friendly_name, path, class_name=None):
    try:
        module = __import__(path, fromlist=[class_name] if class_name else []) 
        MODULOS_STATUS[friendly_name] = "✅ ONLINE"
        return getattr(module, class_name) if class_name else module
    except Exception as e:
        MODULOS_STATUS[friendly_name] = f"❌ OFFLINE ({e})"
        return None

SystemMonitor = safe_import("Monitor", "features.system_monitor", "SystemMonitor")
SystemScanner = safe_import("Scanner", "features.system_scanner", "SystemScanner")
TelegramBotUplink = safe_import("Uplink", "features.telegram_uplink", "TelegramBotUplink")
WeatherSystem = safe_import("Clima", "features.weather_system", "WeatherSystem")
AirTrafficControl = safe_import("Radar", "features.air_traffic", "AirTrafficControl")
FrontlineIntel = safe_import("Intel_War", "features.intel_war", "IntelWar") # Atualizado para o nome do arquivo que você mandou
AstroDefense = safe_import("Astro", "features.astro_defense", "AstroDefenseSystem")
VolcanoMonitor = safe_import("Magma", "features.volcano_monitor", "VolcanoMonitor")
LocalLlamaBrain = safe_import("Cérebro_Dolphin", "features.local_brain", "LocalLlamaBrain")

# =============================================================================
# 6. R2 CORE
# =============================================================================
class R2Core:
    def __init__(self, token):
        self.token = token
        self.running = True
        self.start_time = datetime.now()
        
        self.main_loop = None
        self.update_queue = None
        self.estados_espera = {} # Substitui o context.user_data do bot antigo

        # Instancia Módulos
        self.scanner = SystemScanner() if SystemScanner else None
        self.monitor = SystemMonitor(self) if SystemMonitor else None
        self.weather_ops = WeatherSystem(api_key="SUA_CHAVE") if WeatherSystem else None
        self.radar_ops = AirTrafficControl() if AirTrafficControl else None
        self.intel_ops = FrontlineIntel() if FrontlineIntel else None
        self.astro_ops = AstroDefense() if AstroDefense else None
        self.volcano_ops = VolcanoMonitor() if VolcanoMonitor else None

        self.brain = None
        if LocalLlamaBrain:
            try:
                self.brain = LocalLlamaBrain()
            except Exception as e:
                logging.error(f"Erro IA: {e}")

        self.uplink = None
        if TelegramBotUplink:
            try:
                self.uplink = TelegramBotUplink(self)
            except Exception as e:
                logging.error(f"Erro Uplink: {e}")

    async def boot_sequence(self):
        self.main_loop = asyncio.get_running_loop()
        self.update_queue = asyncio.Queue()

        print("\n" + "═"*70)
        print(f"🤖 R2 ASSISTANT CORE - PROTOCOLO INTEGRAL")
        print("═"*70)
        for mod, st in MODULOS_STATUS.items(): print(f" > {mod.ljust(15)}: {st}")

        if self.uplink:
            asyncio.create_task(self._command_consumer())
            if hasattr(self.uplink, 'iniciar_sistema'):
                self.uplink.iniciar_sistema()
            print("\n🟢 [STATUS]: R2 totalmente operacional.")
            while self.running: await asyncio.sleep(1)

    async def _command_consumer(self):
        while self.running:
            item = await self.update_queue.get()
            try:
                await self.processar_comando_remoto(item['comando'], item['sender_id'])
            except Exception as e:
                logging.error(f"Erro na execução tática: {e}")
            self.update_queue.task_done()

    async def processar_comando_remoto(self, comando, sender_id):
        comando_limpo = comando.lower().strip()

        # 1. TRATAMENTO DE ESTADOS DE ESPERA (Cidades para Radar/Clima)
        if sender_id in self.estados_espera:
            acao = self.estados_espera[sender_id]
            del self.estados_espera[sender_id]
            
            if acao == 'aguardando_radar' and self.radar_ops:
                self.uplink.enviar_mensagem_ativa(f"✈️ Iniciando radar para {comando}...", sender_id)
                msg, img = await asyncio.to_thread(self.radar_ops.gerar_radar, comando)
                if img: self.uplink.enviar_foto_ativa(img, msg, sender_id)
                else: self.uplink.enviar_mensagem_ativa(msg, sender_id)
                return
            elif acao == 'aguardando_clima' and self.weather_ops:
                self.uplink.enviar_mensagem_ativa(f"⛈️ Buscando clima para {comando}...", sender_id)
                res = await asyncio.to_thread(self.weather_ops.obter_clima, comando)
                self.uplink.enviar_mensagem_ativa(res, sender_id)
                return

        # 2. ROTEAMENTO DE BOTÕES (Menu Tático)
        if comando_limpo == 'status':
            import psutil
            res = f"📊 *STATUS*\nCPU: {psutil.cpu_percent()}%\nRAM: {psutil.virtual_memory().percent}%"
            self.uplink.enviar_mensagem_ativa(res, sender_id)
            
        elif comando_limpo == 'pedir_voos' or comando_limpo == 'radar':
            self.estados_espera[sender_id] = 'aguardando_radar'
            self.uplink.enviar_mensagem_ativa("✈️ Envie o nome da cidade para o radar:", sender_id)
            
        elif comando_limpo == 'pedir_cidade' or comando_limpo == 'clima':
            self.estados_espera[sender_id] = 'aguardando_clima'
            self.uplink.enviar_mensagem_ativa("⛈️ Envie o nome da cidade para o clima:", sender_id)
            
        elif comando_limpo == 'terremotos' or comando_limpo == 'sismos':
            if getattr(self, 'seismico', None) or 'GeoSeismicSystem' in MODULOS_STATUS:
                # Adapte para a sua classe sismica real
                self.uplink.enviar_mensagem_ativa("🌍 Consultando sensores sísmicos...", sender_id)
            
        elif comando_limpo == 'intel ucrania' and self.intel_ops:
            self.uplink.enviar_mensagem_ativa("🇺🇦 Extraindo intel militar da Ucrânia...", sender_id)
            msg, img = await asyncio.to_thread(self.intel_ops.get_war_report_with_screenshot, "ucrania")
            if img: self.uplink.enviar_foto_ativa(img, msg, sender_id)
            else: self.uplink.enviar_mensagem_ativa(msg, sender_id)

        # 3. ROTA DE INTELIGÊNCIA ARTIFICIAL (Conversa livre)
        elif self.brain:
            self.uplink.enviar_mensagem_ativa("🧠 Processando...", sender_id)
            resposta = await asyncio.to_thread(self.brain.think, comando)
            self.uplink.enviar_mensagem_ativa(resposta, sender_id)


def main():
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    r2 = R2Core(TOKEN_ARG)
    try:
        asyncio.run(r2.boot_sequence())
    except KeyboardInterrupt:
        print("\n🛑 Desligando...")

if __name__ == "__main__":
    main()
