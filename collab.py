import os
import sys
import asyncio
import subprocess
from pathlib import Path

# =============================================================================
# 1. SETUP DE AMBIENTE (Injetando dependências dos seus módulos)
# =============================================================================
def setup_full_system():
    print("🚀 [SISTEMA] Preparando ambiente para módulos integrados...")
    packages = [
        "llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121",
        "python-telegram-bot", "huggingface_hub", "geopy", "matplotlib", 
        "requests", "beautifulsoup4", "feedparser", "cloudscraper", "playwright"
    ]
    for pkg in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *pkg.split(), "--quiet"])
    
    # Instala o navegador para o IntelWar
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

# Diretório onde este script está
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Opcional: criar __init__.py
init_file = os.path.join(SCRIPT_DIR, "__init__.py")
if not os.path.exists(init_file):
    with open(init_file, "w") as f:
        f.write("# R2 package\n")

# Importações locais com fallback
modules = {}
required_modules = [
    ("radar_api", "RadarAereoAPI"),
    ("weather_system", "WeatherSystem"),
    ("geo_seismic", "GeoSeismicSystem"),
    ("volcano_monitor", "VolcanoMonitor"),
    ("intel_war", "IntelWar"),
    ("news_briefing", "NewsBriefing"),
]

for mod_name, class_name in required_modules:
    try:
        module = __import__(mod_name)
        cls = getattr(module, class_name)
        modules[mod_name] = cls
        print(f"✅ {mod_name} carregado.")
    except ImportError as e:
        print(f"⚠️ Falha ao carregar {mod_name}: {e}")
        # Cria uma classe dummy
        def dummy(self, *args, **kwargs):
            return f"⚠️ Módulo {mod_name}.py indisponível.", None
        dummy_class = type(class_name, (), {"__init__": lambda self: None})
        setattr(dummy_class, "gerar_radar" if "radar" in mod_name else 
                ("obter_clima" if "weather" in mod_name else 
                 ("get_seismic_data_text" if "seismic" in mod_name else
                  ("get_volcano_report" if "volcano" in mod_name else
                   ("get_war_report_with_screenshot" if "intel" in mod_name else
                    "get_top_headlines")))), dummy)
        modules[mod_name] = dummy_class

# Atribui às variáveis globais
RadarAereoAPI = modules["radar_api"]
WeatherSystem = modules["weather_system"]
GeoSeismicSystem = modules["geo_seismic"]
VolcanoMonitor = modules["volcano_monitor"]
IntelWar = modules["intel_war"]
NewsBriefing = modules["news_briefing"]

# =============================================================================
# 2. INICIALIZAÇÃO DE COMPONENTES
# =============================================================================
TOKEN = sys.argv[1] if len(sys.argv) > 1 else None
AUTHORIZED_USERS = {8117345546, 8379481331}

# IA Llama-3
from huggingface_hub import hf_hub_download
model_path = hf_hub_download(repo_id="MaziyarPanahi/Llama-3-8B-Instruct-v0.1-GGUF", filename="Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf", local_dir="/content/models")
llm = Llama(model_path=model_path, n_gpu_layers=-1, n_ctx=2048, verbose=False)

# Instâncias dos seus sistemas
radar = RadarAereoAPI()
clima = WeatherSystem(api_key="SUA_API_KEY_AQUI") # Lembre de colocar sua key
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