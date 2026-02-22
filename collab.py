import os
import sys
import asyncio
import subprocess
from pathlib import Path

# =============================================================================
# 1. SETUP DE AMBIENTE (Injetando dependências dos seus módulos)
# =============================================================================
def setup_full_system():
    print("🚀 [SISTEMA] Preparando ambiente...")
    packages = [
        "llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121",
        "python-telegram-bot", "huggingface_hub", "geopy", "matplotlib", 
        "requests", "beautifulsoup4", "feedparser", "cloudscraper", "playwright",
        "ping3", "psutil", "speedtest-cli", "opencv-python", "pyautogui", "cryptography"
    ]
    for pkg in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *pkg.split(), "--quiet"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    print("✅ [SISTEMA] Todos os módulos estão prontos.")

try:
    from llama_cpp import Llama
    from telegram import Update
    from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
except ImportError:
    setup_full_system()
    from llama_cpp import Llama
    from telegram import Update
    from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# =============================================================================
# CONFIGURAÇÃO DO PATH E IMPORTS LOCAIS
# =============================================================================
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Cria __init__.py na raiz (opcional)
init_file = os.path.join(SCRIPT_DIR, "__init__.py")
if not os.path.exists(init_file):
    with open(init_file, "w") as f:
        f.write("# R2 package\n")

# Classes fallback (definidas antes)
class DummyRadarAereoAPI:
    def __init__(self): pass
    def gerar_radar(self, cidade_nome):
        return "⚠️ Módulo radar_api.py não disponível.", None

class DummyWeatherSystem:
    def __init__(self, api_key=None): pass  # aceita api_key, mas ignora
    def obter_clima(self, cidade_input):
        return "⚠️ Módulo weather_system.py não disponível."

class DummyGeoSeismicSystem:
    def __init__(self): pass
    def get_seismic_data_text(self):
        return "⚠️ Módulo geo_seismic.py não disponível."

class DummyVolcanoMonitor:
    def __init__(self): pass
    def get_volcano_report(self):
        return "⚠️ Módulo volcano_monitor.py não disponível."

class DummyIntelWar:
    def __init__(self): pass
    def get_war_report_with_screenshot(self, setor_input="global"):
        return "⚠️ Módulo intel_war.py não disponível.", None
    def get_pizzint_text_only(self):
        return "⚠️ Módulo intel_war.py não disponível."

class DummyNewsBriefing:
    def __init__(self): pass
    def get_top_headlines(self):
        return "⚠️ Módulo news_briefing.py não disponível."

modules = {}
required = [
    ("features.radar_api", "RadarAereoAPI", DummyRadarAereoAPI),
    ("features.weather_system", "WeatherSystem", DummyWeatherSystem),
    ("features.geo_seismic", "GeoSeismicSystem", DummyGeoSeismicSystem),
    ("features.volcano_monitor", "VolcanoMonitor", DummyVolcanoMonitor),
    ("features.intel_war", "IntelWar", DummyIntelWar),
    ("features.news_briefing", "NewsBriefing", DummyNewsBriefing),
]

for mod_path, class_name, dummy_class in required:
    try:
        module = __import__(mod_path, fromlist=[class_name])
        cls = getattr(module, class_name)
        modules[mod_path.split('.')[-1]] = cls
        print(f"✅ {mod_path} carregado com sucesso.")
    except ImportError as e:
        print(f"⚠️ Falha ao carregar {mod_path}: {e}. Usando fallback.")
        modules[mod_path.split('.')[-1]] = dummy_class
    except Exception as e:
        print(f"❌ Erro inesperado ao carregar {mod_path}: {e}. Usando fallback.")
        modules[mod_path.split('.')[-1]] = dummy_class

RadarAereoAPI = modules["radar_api"]
WeatherSystem = modules["weather_system"]
GeoSeismicSystem = modules["geo_seismic"]
VolcanoMonitor = modules["volcano_monitor"]
IntelWar = modules["intel_war"]
NewsBriefing = modules["news_briefing"]

# =============================================================================
# 2. INICIALIZAÇÃO DE COMPONENTES
# =============================================================================
from huggingface_hub import hf_hub_download
import os
from getpass import getpass

# Obter token: prioridade para argumento da linha de comando, depois variável de ambiente, depois input
if len(sys.argv) > 1:
    TOKEN = sys.argv[1]
else:
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        TOKEN = getpass("Digite o token do Telegram: ")

AUTHORIZED_USERS = {8117345546, 8379481331}

# IA Llama-3
model_path = hf_hub_download(
    repo_id="MaziyarPanahi/Llama-3-8B-Instruct-v0.1-GGUF",
    filename="Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf",
    local_dir="/content/models"
)
llm = Llama(model_path=model_path, n_gpu_layers=-1, n_ctx=2048, verbose=False)

# Instâncias dos seus sistemas
radar = RadarAereoAPI()
clima = WeatherSystem(api_key="SUA_API_KEY_AQUI")   # substitua pela sua chave
seismico = GeoSeismicSystem()
vulcao = VolcanoMonitor()
intel = IntelWar()
noticias = NewsBriefing()

# =============================================================================
# 3. LÓGICA DE COMANDO TÁTICO
# =============================================================================

async def menu_principal(update: Update):
    keyboard = [
        [InlineKeyboardButton("✈️ RADAR DE VOOS", callback_data='radar'),
         InlineKeyboardButton("⛈️ CLIMA", callback_data='clima')],
        [InlineKeyboardButton("🌍 SISMOS", callback_data='sismos'),
         InlineKeyboardButton("🌋 VULCÕES", callback_data='vulcoes')],
        [InlineKeyboardButton("🇺🇦 INTEL UCRÂNIA", callback_data='war_ucrania'),
         InlineKeyboardButton("🇮🇱 INTEL ISRAEL", callback_data='war_israel')],
        [InlineKeyboardButton("📰 NOTÍCIAS", callback_data='news')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🤖 *R2 TÁTICO: OPERACIONAL*\nEscolha um protocolo:", reply_markup=reply_markup, parse_mode='Markdown')

async def processar_botoes(update: Update, context):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'sismos':
        res = seismico.get_seismic_data_text()
        await query.message.reply_text(res, parse_mode='Markdown')
    elif data == 'vulcoes':
        res = vulcao.get_volcano_report()
        await query.message.reply_text(res, parse_mode='Markdown')
    elif data == 'news':
        res = noticias.get_top_headlines()
        await query.message.reply_text(res, parse_mode='Markdown')
    elif data.startswith('war_'):
        setor = data.split('_')[1]
        await query.message.reply_text(f"🛰️ Acessando satélites no setor {setor.upper()}...")
        headlines, path = intel.get_war_report_with_screenshot(setor)
        if path:
            with open(path, 'rb') as f:
                await query.message.reply_photo(photo=f, caption=f"📸 *Relatório {setor.upper()}*\n{headlines}", parse_mode='Markdown')
        else:
            await query.message.reply_text(f"❌ Erro na extração: {headlines}")

async def handle_message(update: Update, context):
    if update.effective_user.id not in AUTHORIZED_USERS: return
    text = update.message.text.lower()

    if "start" in text or "menu" in text:
        await menu_principal(update)
    elif "radar em" in text:
        cidade = text.replace("radar em", "").strip()
        await update.message.reply_text(f"📡 Iniciando varredura em {cidade}...")
        msg, path = radar.gerar_radar(cidade)
        if path:
            with open(path, 'rb') as f:
                await update.message.reply_photo(photo=f, caption=msg)
    else:
        # IA Responde (Llama-3)
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        template = f"<|start_header_id|>system<|end_header_id|>\n\nVocê é o R2.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        output = llm(template, max_tokens=256, stop=["<|eot_id|>"], echo=False)
        await update.message.reply_text(f"🤖: {output['choices'][0]['text'].strip()}")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CallbackQueryHandler(processar_botoes))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🛰️ [UPLINK] R2 Online com Módulos Táticos Integrados.")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    while True: await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())