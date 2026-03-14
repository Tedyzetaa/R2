#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import asyncio
import platform
from pathlib import Path

# =============================================================================
# 1. SETUP DE AMBIENTE E DEPENDÊNCIAS
# =============================================================================
IS_COLAB = 'google.colab' in sys.modules or os.path.exists('/content')

def install_system_deps():
    if IS_COLAB:
        print("📦 Instalando dependências de sistema para o Chromium...")
        try:
            subprocess.check_call(["apt-get", "update", "-qq"])
            subprocess.check_call([
                "apt-get", "install", "-y", "-qq",
                "libnss3", "libatk-bridge2.0-0", "libdrm2", "libxkbcommon0",
                "libgbm1", "libasound2", "libatk1.0-0", "libcups2",
                "libxcomposite1", "libxdamage1", "libxrandr2", "libpango-1.0-0", "libcairo2"
            ])
            # Configuração Playwright
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/content/playwright-browsers'
            subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "--quiet"])
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        except Exception as e:
            print(f"⚠️ Falha nas dependências: {e}")

    packages = [
        "llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121" if IS_COLAB else "llama-cpp-python",
        "python-telegram-bot", "huggingface_hub", "geopy", "matplotlib", 
        "requests", "beautifulsoup4", "feedparser", "cloudscraper", 
        "ping3", "psutil", "speedtest-cli", "opencv-python"
    ]
    for pkg in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + pkg.split() + ["--quiet"])
        except: pass

# Executa instalação inicial
install_system_deps()

from llama_cpp import Llama
from huggingface_hub import hf_hub_download
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, CommandHandler

# =============================================================================
# 2. CONFIGURAÇÃO DE MODELO IA (CORRIGIDO)
# =============================================================================
# Usando o repositório que você validou para evitar Erro 404/401
REPO_ID = "markhneedham/dolphin-2.9-llama3-8b-Q4_K_M-GGUF"
MODEL_FILE = "dolphin-2.9-llama3-8b-q4_k_m.gguf"

print("🛰️ Carregando Inteligência Tática...")
try:
    model_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=MODEL_FILE,
        local_dir="/content/models" if IS_COLAB else "./models"
    )
    llm = Llama(model_path=model_path, n_gpu_layers=-1 if IS_COLAB else 0, n_ctx=2048, verbose=False)
except Exception as e:
    print(f"❌ Erro ao baixar modelo: {e}. Usando fallback...")
    # Fallback automático para garantir que o bot não morra
    model_path = hf_hub_download(repo_id="MaziyarPanahi/Llama-3-8B-Instruct-v0.1-GGUF", 
                                 filename="Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf", 
                                 local_dir="./models")
    llm = Llama(model_path=model_path, n_ctx=2048)

# =============================================================================
# 3. INTEGRAÇÃO DOS SEUS MÓDULOS (RADAR/CLIMA)
# =============================================================================
# Garante que a pasta features seja reconhecida
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path: sys.path.insert(0, SCRIPT_DIR)

def get_module(path, class_name):
    try:
        mod = __import__(path, fromlist=[class_name])
        return getattr(mod, class_name)()
    except Exception as e:
        print(f"⚠️ Módulo {path} indisponível: {e}")
        return None

# Instâncias reais baseadas nos seus arquivos enviados
radar = get_module("features.air_traffic", "AirTrafficControl")
clima = get_module("features.weather_system", "WeatherSystem")
vulcao = get_module("features.volcano_monitor", "VolcanoMonitor")

if clima: clima.api_key = "8db4b830d939639535698f1211e0e980" # Sua chave

# =============================================================================
# 4. LÓGICA DO TELEGRAM E PERSONALIDADE THOMAS SHELBY
# =============================================================================
AUTHORIZED_USERS = {8117345546, 8379481331}

def gerar_resposta_ia(texto):
    system_prompt = (
        "Você é Thomas Shelby. Estratégico, frio, analítico. "
        "Não use emojis em excesso. Responda com autoridade e foco em resultados. "
        "Responda sempre em português brasileiro."
    )
    template = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{texto}<|im_end|>\n<|im_start|>assistant\n"
    output = llm(template, max_tokens=256, stop=["<|im_end|>"])
    return output['choices'][0]['text'].strip()

async def menu_principal(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("✈️ RADAR DE VOOS", callback_data='radar')],
        [InlineKeyboardButton("⛈️ CLIMA", callback_data='clima')],
        [InlineKeyboardButton("🌋 VULCÕES", callback_data='vulcoes')],
        [InlineKeyboardButton("📊 STATUS", callback_data='status')],
    ]
    await update.message.reply_text("🤖 *R2 TÁTICO ONLINE*\nEscolha uma operação:", 
                                   reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def processar_botoes(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == 'radar':
        await query.edit_message_text("✈️ Informe a cidade para o scan de radar:")
        context.user_data['esperando'] = 'radar'
    elif query.data == 'clima':
        await query.edit_message_text("⛈️ Informe a cidade para telemetria climática:")
        context.user_data['esperando'] = 'clima'
    elif query.data == 'vulcoes':
        if vulcao:
            res = await asyncio.to_thread(vulcao.get_volcano_report)
            await context.bot.send_message(chat_id=user_id, text=res, parse_mode='Markdown')

async def lidar_com_mensagem(update: Update, context):
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS: return

    texto = update.message.text
    esperando = context.user_data.get('esperando')

    if esperando == 'radar' and radar:
        del context.user_data['esperando']
        await update.message.reply_text(f"📡 Varrendo espaço aéreo de {texto}...")
        res, qtd, msg = await asyncio.to_thread(radar.radar_scan, texto)
        if res and os.path.exists(res):
            with open(res, 'rb') as f:
                await context.bot.send_photo(chat_id=user_id, photo=f, caption=msg)
        else: await update.message.reply_text(msg)
        return

    if esperando == 'clima' and clima:
        del context.user_data['esperando']
        res = await asyncio.to_thread(clima._gerar_tentativas, texto)
        await update.message.reply_text(res)
        return

    # Resposta IA
    await context.bot.send_chat_action(chat_id=user_id, action="typing")
    resposta = await asyncio.to_thread(gerar_resposta_ia, texto)
    await update.message.reply_text(f"TS: {resposta}")

# =============================================================================
# 5. EXECUÇÃO
# =============================================================================
async def main():
    token = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TELEGRAM_TOKEN")
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", menu_principal))
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
