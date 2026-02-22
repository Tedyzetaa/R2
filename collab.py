import os
import sys
import subprocess
import asyncio
from pathlib import Path

# =============================================================================
# 1. AUTO-CONFIGURAÇÃO TÁTICA (GPU + DEP)
# =============================================================================
def setup_colab():
    print("🚀 [SISTEMA] Iniciando Protocolos de Dependência...")
    
    # 1. Instalação do Córtex Neural com suporte CUDA (Binário pré-compilado)
    print("📦 Instalando Llama-CPP otimizado para GPU T4...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "llama-cpp-python", 
            "--extra-index-url", "https://abetlen.github.io/llama-cpp-python/whl/cu121",
            "--quiet"
        ])
    except:
        os.environ["FORCE_CMAKE"] = "1"
        os.environ["CMAKE_ARGS"] = "-DLLAMA_CUBLAS=on"
        subprocess.check_call([sys.executable, "-m", "pip", "install", "llama-cpp-python", "--quiet"])

    # 2. Outras dependências vitais
    deps = ["python-dotenv", "python-telegram-bot", "requests", "huggingface_hub"]
    for dep in deps:
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--quiet"])
    
    print("✅ [SISTEMA] Ambiente configurado com sucesso.")

# Inicia o setup antes de carregar as bibliotecas pesadas
setup_colab()

from llama_cpp import Llama
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

# =============================================================================
# 2. GESTÃO DE ACESSO (GOOGLE SECRETS)
# =============================================================================
def obter_token():
    try:
        from google.colab import userdata
        token = userdata.get('TELEGRAM_TOKEN')
        if token:
            print("🔑 [SISTEMA] Token recuperado via Google Secrets.")
            return token
    except Exception:
        pass
    
    # Fallback para variável de ambiente ou manual
    return os.getenv("TELEGRAM_TOKEN") or "SEU_TOKEN_AQUI"

TOKEN = obter_token()
AUTHORIZED_USERS = {8117345546, 8379481331}

# =============================================================================
# 3. GESTÃO DO MODELO IA (LLAMA-3)
# =============================================================================
def garantir_modelo():
    from huggingface_hub import hf_hub_download
    repo_id = "MaziyarPanahi/Llama-3-8B-Instruct-v0.1-GGUF"
    filename = "Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf"
    local_dir = Path("/content/models")
    local_dir.mkdir(exist_ok=True)
    
    model_path = local_dir / filename
    if not model_path.exists():
        print(f"📥 [DOWNLOAD] Baixando Llama-3-8B (aprox. 5GB)...")
        path = hf_hub_download(repo_id=repo_id, filename=filename, local_dir=local_dir)
        return path
    print(f"🧠 [CÓRTEX] Modelo detectado em: {model_path}")
    return str(model_path)

# Carrega a IA na VRAM da GPU T4
caminho_ia = garantir_modelo()
print("⚡ [VRAM] Alocando modelo na GPU...")
llm = Llama(model_path=caminho_ia, n_gpu_layers=-1, n_ctx=2048, verbose=False)

# =============================================================================
# 4. PROCESSAMENTO DE MENSAGENS
# =============================================================================
async def responder_ia(prompt):
    """Gera resposta usando o template oficial do Llama-3"""
    template = (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
        f"Você é o R2, um assistente técnico avançado, sarcástico e eficiente.<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
    )
    output = llm(template, max_tokens=512, stop=["<|eot_id|>"], echo=False)
    return output['choices'][0]['text'].strip()

async def telegram_handler(update: Update, context):
    uid = update.effective_user.id
    if uid not in AUTHORIZED_USERS: return

    texto = update.message.text
    print(f"📥 [MSG]: {texto}")

    # Detecta comandos que devem ser feitos pelo PC Local (GUI)
    cmd_local = ["abrir", "print", "screenshot", "volume", "tocar", "clima"]
    if any(c in texto.lower() for c in cmd_local):
        await update.message.reply_text("🖥️ *Comando Físico detectado.* Encaminhando para o terminal local...")
        return

    # Processamento Neural
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        resposta = await responder_ia(texto)
        await update.message.reply_text(f"🤖 *R2:* {resposta}", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Erro no processamento: {e}")

async def run_server():
    if not TOKEN or "SEU_TOKEN" in TOKEN:
        print("❌ [ERRO] Token do Telegram ausente! Configure nas Secrets do Colab.")
        return

    print("🛰️ [UPLINK] Servidor R2 ativo no Google Colab.")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_handler))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("🛑 Servidor desligado.")