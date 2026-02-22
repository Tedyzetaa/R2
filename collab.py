import os
import sys
import asyncio
import subprocess
from pathlib import Path
from telegram.request import HTTPXRequest

# 1. AJUSTE DE PATH (Para carregar seus módulos .py do repo)
# Isso permite que você faça 'import modulo_x' de qualquer arquivo no seu GitHub
sys.path.append(os.getcwd())

def setup():
    print("🚀 [SISTEMA] Verificando integridade dos módulos...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "llama-cpp-python", "--extra-index-url", "https://abetlen.github.io/llama-cpp-python/whl/cu121", "--quiet"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot", "huggingface_hub", "python-dotenv", "--quiet"])

try:
    from llama_cpp import Llama
    from telegram import Update
    from telegram.ext import Application, MessageHandler, filters
    # Tente importar seus módulos específicos aqui para teste
    # import seu_modulo_personalizado 
except ImportError:
    setup()
    from llama_cpp import Llama
    from telegram import Update
    from telegram.ext import Application, MessageHandler, filters

# =============================================================================
# CARREGAMENTO DINÂMICO DE MÓDULOS DO REPOSITÓRIO
# =============================================================================
def listar_modulos():
    arquivos = [f for f in os.listdir('.') if f.endswith('.py') and f != 'collab.py']
    print(f"📦 [MÓDULOS ENCONTRADOS]: {arquivos}")
    return arquivos

MODULOS_ATIVOS = listar_modulos()

# =============================================================================
# CONFIGURAÇÕES E TOKEN (VERSÃO INFALÍVEL)
# =============================================================================
def get_token():
    # 1. Tenta buscar na variável de ambiente (injetada pela célula do Colab)
    token = os.environ.get('TELEGRAM_TOKEN')
    if token and len(token) > 10:
        return token

    # 2. Tenta buscar nas Secrets do Colab
    try:
        from google.colab import userdata
        token = userdata.get('TELEGRAM_TOKEN')
        if token: return token
    except:
        pass

    # 3. Tenta buscar em um arquivo temporário (plano B)
    if os.path.exists("/content/token.txt"):
        with open("/content/token.txt", "r") as f:
            return f.read().strip()
            
    return None

TOKEN = get_token()
AUTHORIZED_USERS = {8117345546, 8379481331}

from huggingface_hub import hf_hub_download
model_path = hf_hub_download(repo_id="MaziyarPanahi/Llama-3-8B-Instruct-v0.1-GGUF", filename="Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf", local_dir="/content/models")
llm = Llama(model_path=model_path, n_gpu_layers=-1, n_ctx=2048, verbose=False)

# =============================================================================
# LÓGICA DE PROCESSAMENTO (IA + MÓDULOS)
# =============================================================================
async def handler(update: Update, context):
    if update.effective_user.id not in AUTHORIZED_USERS: return
    
    user_input = update.message.text
    
    # Exemplo de como usar os módulos:
    # Se o input for "status", você pode chamar uma função de outro arquivo seu
    if user_input.lower() == "status":
        msg_modulos = f"🛰️ Servidor Colab Ativo.\nMódulos detectados: {len(MODULOS_ATIVOS)}"
        await update.message.reply_text(msg_modulos)
        return

    # Processamento padrão pela IA
    template = f"<|start_header_id|>system<|end_header_id|>\n\nVocê é o R2. Use as ferramentas disponíveis.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    output = llm(template, max_tokens=256, stop=["<|eot_id|>"], echo=False)
    await update.message.reply_text(f"🤖 *R2:* {output['choices'][0]['text'].strip()}", parse_mode='Markdown')

async def main():
    t_request = HTTPXRequest(connect_timeout=30, read_timeout=30)
    app = Application.builder().token(TOKEN).request(t_request).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    
    print("🛰️ [UPLINK] R2 Online. Módulos integrados ao Path.")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())