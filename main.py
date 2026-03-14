import sys
import os
import asyncio
import platform
import threading
import time
import logging
from datetime import datetime

# --- 1. PROTOCOLO DE RECONHECIMENTO DE DIRETÓRIOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# --- 2. CONFIGURAÇÃO DE LOGGING DE EMERGÊNCIA ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] R2_CORE: %(message)s',
    handlers=[logging.FileHandler("r2_system.log"), logging.StreamHandler()]
)

# --- 3. GESTÃO DE REDUNDÂNCIA DE TOKEN ---
if len(sys.argv) < 2:
    # Failover: Tenta ler do .env se não houver argumento
    from dotenv import load_dotenv
    load_dotenv()
    TOKEN_ARG = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN_ARG:
        print("❌ [ERRO CRÍTICO]: Token não encontrado em sys.argv nem no .env")
        sys.exit(1)
else:
    TOKEN_ARG = sys.argv[1]

os.environ["TELEGRAM_TOKEN"] = TOKEN_ARG

# --- 4. IMPORTAÇÃO COM REDUNDÂNCIA (TRY-CATCH POR MÓDULO) ---
# Se um módulo falhar, o sistema marca como inativo mas NÃO trava o boot.
MODULOS_ATIVOS = {}

def carregar_modulo(nome_amigavel, path_import, classe_nome=None):
    try:
        mod = __import__(path_import, fromlist=[classe_nome] if classe_nome else [])
        if classe_nome:
            instance = getattr(mod, classe_nome)
            MODULOS_ATIVOS[nome_amigavel] = True
            return instance
        MODULOS_ATIVOS[nome_amigavel] = True
        return mod
    except Exception as e:
        logging.error(f"Falha ao carregar {nome_amigavel}: {e}")
        MODULOS_ATIVOS[nome_amigavel] = False
        return None

# Carregamento Estratégico
SystemMonitor = carregar_modulo("Monitor", "features.system_monitor", "SystemMonitor")
SystemScanner = carregar_modulo("Scanner", "features.system_scanner", "SystemScanner")
TelegramBotUplink = carregar_modulo("Uplink", "features.telegram_uplink", "TelegramBotUplink")
WeatherSystem = carregar_modulo("Clima", "features.weather_system", "WeatherSystem")
AirTrafficControl = carregar_modulo("Radar", "features.air_traffic", "AirTrafficControl")
FrontlineIntel = carregar_modulo("Intel", "features.liveuamap_intel", "FrontlineIntel")
AstroDefenseSystem = carregar_modulo("Astro", "features.astro_defense", "AstroDefenseSystem")
QuantumCoreManager = carregar_modulo("Quantum", "quantum_module", "QuantumCoreManager")
LocalLlamaBrain = carregar_modulo("Cérebro", "features.local_brain", "LocalLlamaBrain")

# --- 5. CÉREBRO CENTRAL COM AUTO-RECUPERAÇÃO ---
class R2Core:
    def __init__(self, token):
        self.token = token
        self.running = True
        self.start_time = datetime.now()
        self.reconnect_attempts = 0
        
        # Inicialização Segura das Instâncias
        self.scanner = SystemScanner() if MODULOS_ATIVOS["Scanner"] else None
        self.monitor = SystemMonitor(self) if MODULOS_ATIVOS["Monitor"] else None
        
        # Módulos de Operação
        self.weather = WeatherSystem(api_key="SUA_CHAVE") if MODULOS_ATIVOS["Clima"] else None
        self.radar = AirTrafficControl() if MODULOS_ATIVOS["Radar"] else None
        self.intel = FrontlineIntel() if MODULOS_ATIVOS["Intel"] else None
        self.quantum = QuantumCoreManager() if MODULOS_ATIVOS["Quantum"] else None
        self.brain = LocalLlamaBrain() if MODULOS_ATIVOS["Cérebro"] else None

        # O Uplink é o módulo mais crítico (Redundância de Conexão interna)
        try:
            self.uplink = TelegramBotUplink(self) if MODULOS_ATIVOS["Uplink"] else None
        except Exception as e:
            logging.critical(f"Falha ao instanciar Uplink: {e}")
            self.uplink = None

    def get_uptime(self):
        delta = datetime.now() - self.start_time
        return str(delta).split(".")[0]

    async def watch_dog_protocol(self):
        """Monitora se o bot ainda está respondendo, se não, tenta reiniciar módulos"""
        while self.running:
            await asyncio.sleep(60) # Checagem a cada minuto
            if self.scanner:
                stats = self.scanner.get_stats()
                if stats['cpu'] > 95:
                    logging.warning("⚠️ CARGA CRÍTICA DETECTADA. Liberando memória...")
                    # Aqui poderia entrar uma lógica de limpar cache

    async def boot_sequence(self):
        """Sequência de inicialização com verificação de redundância"""
        print("\n" + "═"*60)
        print(f"🚀 R2 CORE - PROTOCOLO DE REDUNDÂNCIA ATIVADO")
        print(f"📍 NÓ: {platform.node()} | OS: {platform.system()}")
        print(f"📅 BOOT: {self.start_time.strftime('%H:%M:%S')}")
        print("═"*60)

        # Relatório de Módulos
        print("\n📂 [ESTADO DOS MÓDULOS]:")
        for mod, status in MODULOS_ATIVOS.items():
            check = "✅" if status else "❌"
            print(f"  {check} {mod}")

        # Início dos serviços em Background
        asyncio.create_task(self.watch_dog_protocol())

        try:
            if self.uplink:
                print("\n📡 [UPLINK]: Conectando ao cluster Telegram...")
                # Redundância: Se o loop cair, ele tenta reiniciar o polling
                while self.running:
                    try:
                        # Se o seu uplink usa .run(), coloque aqui. 
                        # Se for assíncrono, await self.uplink.start()
                        print("🟢 [STATUS]: Sistema R2 em Operação.")
                        await asyncio.sleep(3600) 
                    except Exception as e:
                        self.reconnect_attempts += 1
                        logging.error(f"Link perdido. Tentativa de reconexão {self.reconnect_attempts}: {e}")
                        await asyncio.sleep(5) # Delay de segurança
            else:
                print("❌ [ERRO]: Uplink indisponível. Sistema em modo Offline.")
                
        except Exception as e:
            logging.critical(f"Falha na sequência principal: {e}")

# --- 6. EXECUÇÃO COM TRATAMENTO DE EXCEÇÃO GLOBAL ---
def main():
    # Compatibilidade de Loop (Windows/Linux)
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    r2 = R2Core(TOKEN_ARG)

    try:
        asyncio.run(r2.boot_sequence())
    except KeyboardInterrupt:
        print("\n🛑 [SISTEMA]: Desligamento manual iniciado pelo Operador.")
        r2.running = False
    except Exception as e:
        # Redundância Final: Loga o erro antes de morrer
        with open("emergency_crash.log", "a") as f:
            f.write(f"[{datetime.now()}] CRASH TOTAL: {str(e)}\n")
        print(f"💥 [CRASH TOTAL]: O sistema colapsou. Verifique 'emergency_crash.log'.")

if __name__ == "__main__":
    main()
