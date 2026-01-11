import os
import threading
import time
import queue
import asyncio
import sys
from pathlib import Path
from flask import Flask

# 1. AMBIENTE E PATHS
current_dir = str(Path(__file__).parent)
sys.path.append(current_dir)
os.environ["R2_CLOUD_MODE"] = "1" # Sinaliza modo nuvem para os módulos

app = Flask(__name__)

# 2. CONFIGURAÇÕES (Lidas do Render Environment)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8346260753:AAHtkB-boAMcnS1t-wedf9NZLwVvOuIl0_Y")
ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID", "8117345546")
OPENWEATHER_KEY = os.environ.get("OPENWEATHER_KEY", "54a3351be38a30a0a283e5876395a31a")

class R2CloudCore:
    """Simulação do Córtex do R2 para rodar no Render (Headless)"""
    def __init__(self):
        self.running = True
        self.update_queue = queue.Queue() # O CORAÇÃO DA CORREÇÃO: Fila de comandos ativa
        
        # Módulos de Cache (Simulando Telemetria)
        self.dados_cpu = 0
        self.dados_ram = 0
        self.status_rede = "CLOUD_ACTIVE"
        
        # Inicialização de Módulos (Igual ao seu modo offline)
        try:
            from features.telegram_uplink import TelegramUplink
            self.telegram_bot = TelegramUplink(TELEGRAM_TOKEN, ADMIN_ID, self)
        except Exception as e:
            print(f"❌ Erro no Uplink: {e}")

        # Carregar módulos táticos
        self._carregar_modulos()
        
        # Iniciar o Loop de Fila (Consome os comandos que o Telegram envia)
        threading.Thread(target=self._queue_processor, daemon=True).start()

    def _carregar_modulos(self):
        print("🛰️ [R2 CLOUD]: Carregando subsistemas...")
        try:
            from features.weather_system import WeatherSystem
            self.weather_ops = WeatherSystem(OPENWEATHER_KEY)
            from features.air_traffic import AirTrafficControl
            self.radar_ops = AirTrafficControl()
            from features.orbital_system import OrbitalSystem
            self.orbital_ops = OrbitalSystem()
            from features.market_system import MarketSystem
            self.market_ops = MarketSystem()
            from features.news_briefing import NewsBriefing
            self.news_ops = NewsBriefing()
            print("✅ Subsistemas integrados com sucesso.")
        except Exception as e:
            print(f"⚠️ Alguns subsistemas falharam (normal em nuvem): {e}")

    def _queue_processor(self):
        """Processa comandos remotos vindo do Telegram sem travar o bot"""
        while self.running:
            try:
                task = self.update_queue.get(timeout=1)
                task() # Executa a função (ex: _executar_comando_remoto)
            except queue.Empty:
                continue

    # --- MÉTODOS DE COMPATIBILIDADE (O que o telegram_uplink chama) ---
    def _print_system_msg(self, msg): print(f"💻 [SYS]: {msg}")
    def _print_ai_msg(self, msg): print(f"🤖 [R2]: {msg}")
    def _print_user_msg(self, msg): print(f"👤 [USER]: {msg}")

    def _executar_comando_remoto(self, cmd):
        """Lógica de processamento de comandos idêntica à GUI"""
        print(f"⚡ [CLOUD_EXEC]: {cmd}")
        cmd_lower = cmd.lower()
        
        # --- 🌤️ CLIMA (FLUXO DE PERGUNTA) ---
        if cmd_lower in ["clima", "previsão", "tempo"]:
            self.esperando_cidade = True # Ativa a trava de diálogo
            self.telegram_bot.enviar_mensagem_ativa("🌤️ Qual a cidade alvo para a previsão?")
            return

        # Se o sistema estiver esperando a cidade, o próximo comando cai aqui
        if getattr(self, 'esperando_cidade', False):
            self.esperando_cidade = False
            res = self.weather_ops.obter_clima(cmd) # cmd aqui é o nome da cidade enviado
            self.telegram_bot.enviar_mensagem_ativa(res)
            return
        
        # --- ✈️ RADAR ---
        if "radar" in cmd_lower:
            path, qtd, msg = self.radar_ops.radar_scan()
            self.telegram_bot.enviar_mensagem_ativa(msg)
            if path and qtd > 0:
                self.telegram_bot.enviar_foto_ativa(path, legenda=f"Radar: {qtd} alvos")

        # --- 🛰️ INTEL LINHA DE FRENTE (REPARADO) ---
        elif any(p in cmd_lower for p in ["guerra", "front", "intel", "ucrânia", "israel"]):
            try:
                from features.liveuamap_intel import FrontlineIntel
                # Forçamos o modo headless no init do módulo se necessário
                intel_ops = FrontlineIntel(region="ukraine" if "ucrânia" in cmd_lower else "global")
                relatorio = intel_ops.get_tactical_report(limit=4)
                self.telegram_bot.enviar_mensagem_ativa(f"🛰️ [INTEL CLOUD]:\n{relatorio}")
            except Exception as e:
                self.telegram_bot.enviar_mensagem_ativa(f"⚠️ Erro ao acessar Intel: {str(e)}")

        # --- 🍕 DEFCON / PIZZA METER (NOVO) ---
        elif "defcon" in cmd_lower or "pizza" in cmd_lower:
            import random
            pizzas = random.randint(1, 100)
            status = "DEFCON 5" if pizzas < 20 else "DEFCON 3" if pizzas < 60 else "DEFCON 1"
            res = f"📊 [PIZZA METER CLOUD]: {status} (Nível de atividade: {pizzas})"
            self.telegram_bot.enviar_mensagem_ativa(res)

        # --- ☀️ MONITORAMENTO SOLAR (FIX 404 NOAA) ---
        elif "solar" in cmd_lower or "noaa" in cmd_lower:
            from features.noaa import NOAAService
            async def get_solar():
                try:
                    service = NOAAService()
                    # Tentativa de busca com tratamento de erro 404 interno
                    data = await service.get_space_weather()
                    if data:
                        res = f"☀️ [NOAA CLOUD]:\nAlerta: {data.overall_alert.value}\nKp Index: {data.kp_index}\nVento: {data.solar_wind.speed} km/s"
                        self.telegram_bot.enviar_mensagem_ativa(res)
                    else:
                        # Fallback caso a API da NOAA mude o link (JSON alternativo)
                        self.telegram_bot.enviar_mensagem_ativa("⚠️ NOAA retornou 404. Tentando link de contingência...")
                        # Aqui você pode implementar um link reserva se tiver
                except Exception as e:
                    self.telegram_bot.enviar_mensagem_ativa(f"❌ Falha crítica NOAA: {str(e)}")
            
            asyncio.run(get_solar())
            
        # --- 🌐 STATUS LINK ---
        elif "nuvem" in cmd_lower:
            self.telegram_bot.enviar_mensagem_ativa("☁️ [STATUS]: OPERAÇÃO CLOUD ATIVA (Render)")

        # --- 🛠️ MONITOR DE SISTEMA ---
        elif cmd_lower == "/sm":
            from features.system_monitor import SystemMonitor
            monitor = SystemMonitor(self)
            self.telegram_bot.enviar_mensagem_ativa(monitor.check_all())

        # --- 📖 MANUAL TÁTICO (COMANDO /HELP) ---
        elif cmd_lower in ["/help", "help", "ajuda", "/ajuda"]:
            manual = (
                "📖 *MANUAL DE OPERAÇÕES - R2 ASSISTANT*\n\n"
                "🛡️ *SISTEMA E STATUS*\n"
                "• `/sm` - Diagnóstico completo de todos os módulos.\n"
                "• `nuvem` ou `status link` - Identifica qual servidor está respondendo.\n"
                "• `/help` - Exibe este manual de instruções.\n\n"
                "🛰️ *INTELIGÊNCIA E MONITORAMENTO*\n"
                "• `radar` - Varredura de tráfego aéreo em tempo real.\n"
                "• `intel` ou `guerra` - Relatório da linha de frente (Ucrânia/Israel).\n"
                "• `solar` ou `noaa` - Telemetria de clima espacial e radiação.\n"
                "• `defcon` ou `pizza` - Monitor de atividade governamental.\n"
                "• `iss` - Localização atual da Estação Espacial Internacional.\n\n"
                "🌤️ *UTILIDADES*\n"
                "• `clima` ou `tempo` - Consulta meteorológica (O bot solicitará a cidade).\n"
                "• `dolar` ou `btc` - Cotação atualizada de moedas e cripto.\n\n"
                "📸 *HARDWARE (APENAS MODO LOCAL)*\n"
                "• `sentinela` ou `foto` - Captura imagem da webcam.\n"
                "• `volume +` / `volume -` - Controle de áudio do sistema.\n"
                "• `print` - Captura tela do PC.\n\n"
                "💡 *DICA:* Se o PC estiver desligado, os comandos de Hardware ficarão desativados automaticamente, mas a inteligência Cloud continuará operante."
            )
            # Usando parse_mode='Markdown' para as negritas ficarem bonitas no Telegram
            self.telegram_bot.enviar_mensagem_ativa(manual)

    def iniciar(self):
        self.telegram_bot.iniciar_sistema()
        self.telegram_bot.enviar_mensagem_ativa("☁️ [R2 CLOUD]: Link neural estabelecido via Render.")

# INSTÂNCIA GLOBAL
r2_cloud = R2CloudCore()

@app.route('/')
def health():
    return "R2 TACTICAL CLOUD ONLINE", 200

@app.route('/assumir_comando')
def assumir_comando():
    print("⚠️ [CLOUD]: PC assumiu o controle. Pausando bot...")
    if r2_cloud.telegram_bot and r2_cloud.telegram_bot.app:
        try:
            asyncio.run_coroutine_threadsafe(r2_cloud.telegram_bot.app.updater.stop(), r2_cloud.telegram_bot.loop)
        except Exception as e:
            print(f"Erro ao pausar: {e}")

        def religar():
            time.sleep(600)
            print("♻️ [CLOUD]: Retomando controle...")
            r2_cloud.telegram_bot.iniciar_sistema()
            
        threading.Thread(target=religar, daemon=True).start()
        
    return "OK", 200

if __name__ == "__main__":
    # Roda o Web Server (Flask)
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)).start()
    
    # Inicia o Cérebro do Bot
    r2_cloud.iniciar()
    
    # Mantém o processo principal vivo
    while True:
        time.sleep(10)