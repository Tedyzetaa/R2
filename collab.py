import os
import sys
import subprocess
import asyncio
from pathlib import Path
from telegram.request import HTTPXRequest

# =============================================================================
# AUTO-INSTALAÇÃO DE DEPENDÊNCIAS
# =============================================================================
def setup():
    print("🚀 [SISTEMA] Iniciando Protocolos de Dependência...")
    # Instala o Llama-CPP otimizado para GPU T4
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "llama-cpp-python", 
        "--extra-index-url", "https://abetlen.github.io/llama-cpp-python/whl/cu121", 
        "--quiet"
    ])
    # Instala bibliotecas de comunicação
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "python-telegram-bot", "huggingface_hub", "python-dotenv", "--quiet"
    ])
    print("✅ [SISTEMA] Ambiente configurado.")

# Só instala se não encontrar as bibliotecas
try:
    from llama_cpp import Llama
    from telegram import Update
    from telegram.ext import Application, MessageHandler, filters
except ImportError:
    setup()
    from llama_cpp import Llama
    from telegram import Update
    from telegram.ext import Application, MessageHandler, filters

# =============================================================================
# CONFIGURAÇÕES E TOKEN
# =============================================================================
# Ele tenta ler das Secrets do Colab ou da variável de ambiente injetada
def get_token():
    try:
        from google.colab import userdata
        return userdata.get('TELEGRAM_TOKEN')
    except:
        return os.environ.get('TELEGRAM_TOKEN')

TOKEN = get_token()
AUTHORIZED_USERS = {8117345546, 8379481331}

# =============================================================================
# MODELO IA
# =============================================================================
from huggingface_hub import hf_hub_download
print("🧠 [CÓRTEX] Carregando Llama-3 na GPU...")
model_path = hf_hub_download(
    repo_id="MaziyarPanahi/Llama-3-8B-Instruct-v0.1-GGUF", 
    filename="Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf", 
    local_dir="/content/models"
)
llm = Llama(model_path=model_path, n_gpu_layers=-1, n_ctx=2048, verbose=False)

# =============================================================================
# LÓGICA DO BOT
# =============================================================================
async def handler(update: Update, context):
    if update.effective_user.id not in AUTHORIZED_USERS: return
    
    prompt = update.message.text
    # Template oficial Llama-3 sem o erro de repetição de BoT
    template = (
        f"<|start_header_id|>system<|end_header_id|>\n\n"
        f"Você é o R2, um assistente técnico avançado.<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
    )
    
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        output = llm(template, max_tokens=256, stop=["<|eot_id|>"], echo=False)
        resposta = output['choices'][0]['text'].strip()
        await update.message.reply_text(f"🤖 *R2:* {resposta}", parse_mode='Markdown')
    except Exception as e:
        print(f"Erro no processamento: {e}")

async def main():
    if not TOKEN:
        print("❌ [ERRO] TOKEN NÃO ENCONTRADO!")
        return

    # Configuração de rede robusta para evitar ReadError
    t_request = HTTPXRequest(connect_timeout=30, read_timeout=30)
    app = Application.builder().token(TOKEN).request(t_request).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    
    print("🛰️ [UPLINK] Servidor R2 Online e Operacional.")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Desligando...")