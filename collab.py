#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import asyncio
import random
import time
from pathlib import Path
from getpass import getpass

# =============================================================================
# 1. CONFIGURAÇÃO DE AMBIENTE E DEPENDÊNCIAS
# =============================================================================

def install_sys_deps():
    print("📦 Instalando dependências de sistema para o Chromium...")
    try:
        subprocess.check_call(["apt-get", "update", "-qq"])
        subprocess.check_call([
            "apt-get", "install", "-y", "-qq",
            "libnss3", "libatk-bridge2.0-0", "libdrm2", "libxkbcommon0",
            "libgbm1", "libasound2", "libatk1.0-0", "libcups2",
            "libxcomposite1", "libxdamage1", "libxrandr2", "libpango-1.0-0",
            "libcairo2"
        ])
        print("✅ Dependências de sistema instaladas.")
    except Exception as e:
        print(f"⚠️ Falha ao instalar dependências de sistema: {e}")

def setup_full_system():
    print("🚀 [SISTEMA] Preparando pacotes Python...")
    # Removido duplicatas e organizado
    packages = [
        "llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121",
        "python-telegram-bot", "huggingface_hub", "geopy", "matplotlib", 
        "requests", "beautifulsoup4", "feedparser", "cloudscraper", "playwright",
        "ping3", "psutil", "speedtest-cli", "opencv-python", "cryptography"
    ]
    for pkg in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + pkg.split() + ["--quiet"])
        except Exception as e:
            print(f"⚠️ Falha ao instalar {pkg}: {e}")

# Executa instalações iniciais
if not shutil.which("playwright"):
    install_sys_deps()
    setup_full_system()

# Configuração Playwright
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/content/playwright-browsers'
browsers_path = '/content/playwright-browsers'

if not os.path.exists(browsers_path) or not os.listdir(browsers_path):
    print("📦 Instalando Chromium para Playwright...")
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

# =============================================================================
# 2. PATCH E IMPORTS DE MÓDULOS
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Patch: IntelWar (Garante que o arquivo exista com a lógica correta)
intel_war_path = os.path.join(SCRIPT_DIR, 'features', 'intel_war.py')
os.makedirs(os.path.dirname(intel_war_path), exist_ok=True)

intel_war_content = r'''import os
import requests
import random
import time
from playwright.sync_api import sync_playwright

class IntelWar:
    def __init__(self):
        self.urls = {
            "global": "https://liveuamap.com/",
            "ucrania": "https://ukraine.liveuamap.com/",
            "israel": "https://israelpalestine.liveuamap.com/",
            "defcon": "https://www.defconlevel.com/",
            "pizzint": "https://www.pizzint.watch/"
        }
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]

    def _obter_chave_segura(self, texto_usuario):
        if not texto_usuario: return "global"
        texto = texto_usuario.lower().strip()
        mapa = {"ucrânia": "ucrania", "ucrania": "ucrania", "ukraine": "ucrania",
                "israel": "israel", "gaza": "israel", "palestina": "israel",
                "defcon": "defcon", "pizzint": "pizzint", "global": "global"}
        return mapa.get(texto, "global")

    def get_war_report_with_screenshot(self, setor_input="global"):
        chave = self._obter_chave_segura(setor_input)
        url = self.urls.get(chave, self.urls["global"])
        screenshot_path = os.path.join(os.getcwd(), f"intel_{chave}.png")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(viewport={"width": 1280, "height": 720}, user_agent=random.choice(self.user_agents))
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(5)
                page.screenshot(path=screenshot_path)
                headlines = ""
                if "liveuamap" in url:
                    titles = page.locator(".title").all_text_contents()
                    if titles: headlines = "\n".join([f"• {t.strip()}" for t in titles[:5]])
                browser.close()
                return headlines, screenshot_path
        except Exception as e:
            return f"⚠️ Falha técnica: {str(e)}", None
'''
with open(intel_war_path, 'w') as f: f.write(intel_war_content)

# Fallbacks e Carregamento Dinâmico
class DummyModule:
    def __getattr__(self, name):
        return lambda *args, **kwargs: ("⚠️ Módulo indisponível no momento.", None)

def safe_import(mod_path, class_name):
    try:
        module = __import__(mod_path, fromlist=[class_name])
        return getattr(module, class_name)()
    except Exception:
        return DummyModule()

# Imports do Telegram e IA
from llama_cpp import Llama
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from huggingface_hub import hf_hub_download

# =============================================================================
# 3. INICIALIZAÇÃO DE COMPONENTES
# =============================================================================

TOKEN = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TELEGRAM_TOKEN") or getpass("Token Telegram: ")
AUTHORIZED_USERS = {8117345546, 8379481331}

# IA Model
model_path = hf_hub_download(repo_id="MaziyarPanahi/Llama-3-8B-Instruct-v0.1-GGUF", filename="Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf", local_dir="/content/models")
llm = Llama(model_path=model_path, n_gpu_layers=-1, n_ctx=2048, verbose=False)

# Instâncias de Features
radar = safe_import("features.radar_api", "RadarAereoAPI")
clima = safe_import("features.weather_system", "WeatherSystem")
seismico = safe_import("features.geo_seismic", "GeoSeismicSystem")
vulcao = safe_import("features.volcano_monitor", "VolcanoMonitor")
intel = safe_import("features.intel_war", "IntelWar")
noticias = safe_import("features.news_briefing", "NewsBriefing")

# =============================================================================
# 4. LÓGICA DO BOT
# =============================================================================

async def menu_principal(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("✈️ RADAR", callback_data='radar'), InlineKeyboardButton("⛈️ CLIMA", callback_data='clima')],
        [InlineKeyboardButton("🌍 SISMOS", callback_data='sismos'), InlineKeyboardButton("🌋 VULCÕES", callback_data='vulcoes')],
        [InlineKeyboardButton("🇺🇦 INTEL UA", callback_data='intel_ucrania'), InlineKeyboardButton("🇮🇱 INTEL IL", callback_data='intel_israel')],
        [InlineKeyboardButton("📰 NOTÍCIAS", callback_data='news'), InlineKeyboardButton("☀️ SOLAR", callback_data='solar')],
        [InlineKeyboardButton("📊 STATUS", callback_data='status')]
    ]
    await update.message.reply_text("🤖 *R2 TÁTICO* \nSelecione uma operação:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def processar_botoes(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in AUTHORIZED_USERS: return

    data = query.data
    if data == 'radar':
        await query.edit_message_text("✈️ Informe a cidade para o radar:")
        context.user_data['state'] = 'radar'
    elif data == 'clima':
        await query.edit_message_text("⛈️ Informe a cidade para o clima:")
        context.user_data['state'] = 'clima'
    elif data == 'sismos':
        res = await asyncio.to_thread(seismico.get_seismic_data_text)
        await context.bot.send_message(user_id, res, parse_mode='Markdown')
    elif data == 'intel_ucrania':
        await handle_intel(user_id, context, "ucrania")
    elif data == 'intel_israel':
        await handle_intel(user_id, context, "israel")
    elif data == 'status':
        import psutil
        status = f"📊 *SISTEMA*\nCPU: {psutil.cpu_percent()}%\nRAM: {psutil.virtual_memory().percent}%"
        await context.bot.send_message(user_id, status, parse_mode='Markdown')

async def handle_intel(user_id, context, setor):
    await context.bot.send_message(user_id, f"🛰️ Obtendo inteligência: {setor}...")
    texto, path = await asyncio.to_thread(intel.get_war_report_with_screenshot, setor)
    if path and os.path.exists(path):
        with open(path, 'rb') as f:
            await context.bot.send_photo(user_id, photo=f, caption=texto, parse_mode='Markdown')
    else:
        await context.bot.send_message(user_id, texto)

async def lidar_com_mensagem(update: Update, context):
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS: return
    
    texto = update.message.text
    state = context.user_data.get('state')

    if state == 'radar':
        context.user_data['state'] = None
        msg, path = await asyncio.to_thread(radar.gerar_radar, texto)
        if path:
            with open(path, 'rb') as f: await update.message.reply_photo(f, caption=msg)
        else: await update.message.reply_text(msg)
    elif state == 'clima':
        context.user_data['state'] = None
        res = await asyncio.to_thread(clima.obter_clima, texto)
        await update.message.reply_text(res)
    else:
        # Resposta da IA
        await context.bot.send_chat_action(chat_id=user_id, action="typing")
        prompt = f"<|start_header_id|>system<|end_header_id|>\n\nVocê é Kael, estrategista aliado criado por Teddy. Seja direto, maduro e estratégico.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{texto}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        resposta = await asyncio.to_thread(llm, prompt, max_tokens=256, stop=["<|eot_id|>"])
        await update.message.reply_text(resposta['choices'][0]['text'].strip())

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler(["start", "menu"], menu_principal))
    app.add_handler(CallbackQueryHandler(processar_botoes))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lidar_com_mensagem))
    
    print("🛰️ [UPLINK] R2 Online.")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    while True: await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass