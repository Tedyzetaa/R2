#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import asyncio
from pathlib import Path

# =============================================================================
# 1. AMBIENTE E DEPENDÊNCIAS (PROTOCOLO DE INICIALIZAÇÃO)
# =============================================================================
IS_COLAB = 'google.colab' in sys.modules or os.path.exists('/content')

def install_deps():
    print("✨ [SISTEMA]: Verificando integridade dos protocolos de software...")
    packages = [
        "python-telegram-bot", "huggingface_hub", "requests", 
        "psutil", "llama-cpp-python", "geopy", "matplotlib"
    ]
    # No Colab, precisamos de flags específicas para a GPU T4
    if IS_COLAB:
        os.environ["CMAKE_ARGS"] = "-DLLAMA_CUDA=on"
    
    for pkg in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])
        except:
            pass

try:
    from llama_cpp import Llama
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, CommandHandler
    from huggingface_hub import hf_hub_download
except ImportError:
    install_deps()
    from llama_cpp import Llama
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, CommandHandler
    from huggingface_hub import hf_hub_download

# =============================================================================
# 2. CONFIGURAÇÃO J.A.R.V.I.S. (PERSONALIDADE E IA)
# =============================================================================
SYSTEM_PROMPT = (
    "Você é o J.A.R.V.I.S., a inteligência artificial pessoal de Teddy. "
    "Sua personalidade é baseada no assistente de Tony Stark: britânico, polido, "
    "extremamente inteligente e com um senso de humor seco e sutil. "
    "Chame Teddy de 'Senhor' ou 'Sir'. Use termos como 'Protocolos ativados' e 'Telemetria'. "
    "Responda sempre em Português Brasileiro (PT-BR) de forma sofisticada."
)

def gerar_resposta_ia(texto):
    """Processa a entrada do usuário através dos núcleos de processamento neural."""
    template = (
        f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
        f"<|im_start|>user\n{texto}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    
    output = llm(
        template, 
        max_tokens=300, 
        stop=["<|im_end|>", "<|eot_id|>"], 
        temperature=0.7,
        echo=False
    )
    return output['choices'][0]['text'].strip()

# =============================================================================
# 3. DOWNLOAD DO MODELO (UPLINK COM HUGGING FACE)
# =============================================================================
print("🛰️ [UPLINK]: Conectando aos servidores de modelos...")
REPO_ID = "markhneedham/dolphin-2.9-llama3-8b-Q4_K_M-GGUF"
MODEL_FILE = "dolphin-2.9-llama3-8b-q4_k_m.gguf"

model_path = hf_hub_download(
    repo_id=REPO_ID,
    filename=MODEL_FILE,
    local_dir="/content/models" if IS_COLAB else "./models"
)

# Inicializa o LLM com suporte a GPU se disponível
llm = Llama(model_path=model_path, n_gpu_layers=-1 if IS_COLAB else 0, n_ctx=2048, verbose=False)

# =============================================================================
# 4. CARREGAMENTO DOS MÓDULOS TÁTICOS (FEATURES)
# =============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path: sys.path.insert(0, SCRIPT_DIR)

def carregar_modulo(caminho, classe):
    try:
        mod = __import__(caminho, fromlist=[classe])
        return getattr(mod, classe)()
    except Exception as e:
        print(f"⚠️ [AVISO]: Módulo {caminho} não pôde ser inicializado: {e}")
        return None

radar = carregar_modulo("features.air_traffic", "AirTrafficControl")
clima = carregar_modulo("features.weather_system", "WeatherSystem")
vulcao = carregar_modulo("features.volcano_monitor", "VolcanoMonitor")

if clima: clima.api_key = "8db4b830d939639535698f1211e0e980"

# =============================================================================
# 5. HANDLERS DO TELEGRAM (INTERFACE COM O SENHOR)
# =============================================================================
AUTHORIZED_USERS = {8117345546, 8379481331}

async def start(update: Update, context):
    if update.effective_user.id not in AUTHORIZED_USERS: return
    keyboard = [
        [InlineKeyboardButton("✈️ RADAR", callback_data='radar'), InlineKeyboardButton("⛈️ CLIMA", callback_data='clima')],
        [InlineKeyboardButton("🌋 VULCÕES", callback_data='vulcao'), InlineKeyboardButton("📊 STATUS", callback_data='status')]
    ]
    await update.message.reply_text(
        "Bem-vindo de volta, Senhor. Todos os sistemas do R2 estão operacionais. Como posso ajudar?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def processar_botoes(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'radar':
        await query.edit_message_text("Entendido. Por favor, forneça as coordenadas ou o nome da cidade para o scan aéreo:")
        context.user_data['esperando'] = 'radar'
    elif query.data == 'clima':
        await query.edit_message_text("Acessando satélites meteorológicos. Qual a localização, Sir?")
        context.user_data['esperando'] = 'clima'
    elif query.data == 'status':
        import psutil
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        await query.edit_message_text(f"📊 DIAGNÓSTICO DO SISTEMA:\n\nCPU: {cpu}%\nRAM: {ram}%\nStatus: Nominal")

async def lidar_com_mensagem(update: Update, context):
    if update.effective_user.id not in AUTHORIZED_USERS: return
    
    texto = update.message.text
    esperando = context.user_data.get('esperando')

    # Lógica de Módulos
    if esperando == 'radar' and radar:
        del context.user_data['esperando']
        await update.message.reply_text("Iniciando varredura de vetores aéreos...")
        path, qtd, msg = await asyncio.to_thread(radar.radar_scan, texto)
        if path and os.path.exists(path):
            with open(path, 'rb') as f:
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=f, caption=msg)
        else: await update.message.reply_text(msg)
        return

    if esperando == 'clima' and clima:
        del context.user_data['esperando']
        res = await asyncio.to_thread(clima._gerar_tentativas, texto)
        await update.message.reply_text(res)
        return

    # Resposta JARVIS
    await update.message.reply_chat_action("typing")
    resposta = await asyncio.to_thread(gerar_resposta_ia, texto)
    await update.message.reply_text(resposta)

# =============================================================================
# 6. INICIALIZAÇÃO DO UPLINK
# =============================================================================
async def main():
    token = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("❌ [ERRO]: Token ausente.")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(processar_botoes))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lidar_com_mensagem))
    
    print("📡 [SISTEMA]: JARVIS online e aguardando ordens.")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    while True: await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
