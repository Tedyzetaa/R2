import os
import sys
import subprocess
import asyncio
from pathlib import Path

# =============================================================================
# 1. CONFIGURAÇÃO DE AMBIENTE E DEPENDÊNCIAS
# =============================================================================
def setup_colab():
    print("🚀 [SISTEMA] Iniciando Protocolos de Dependência...")
    
    # 1. Instala dependências básicas
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv", "python-telegram-bot", "requests", "huggingface_hub", "--quiet"])

    # 2. Instala llama-cpp-python usando um binário pré-compilado para CUDA 12.x (Padrão do Colab)
    # Isso evita o erro de "Building wheel"
    print("📦 Instalando Cérebro Neural (Llama-CPP) otimizado para GPU...")
    try:
        # Comando para instalar versão com suporte a CUDA sem compilar do zero
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "llama-cpp-python", 
            "--extra-index-url", "https://abetlen.github.io/llama-cpp-python/whl/cu121"
        ])
    except:
        # Fallback caso o link acima falhe
        os.environ["FORCE_CMAKE"] = "1"
        os.environ["CMAKE_ARGS"] = "-DLLAMA_CUBLAS=on"
        subprocess.check_call([sys.executable, "-m", "pip", "install", "llama-cpp-python", "--no-cache-dir"])
        
    print("✅ [SISTEMA] Ambiente configurado com sucesso.")

# =============================================================================
# 2. DOWNLOAD AUTOMÁTICO DO MODELO LLAMA
# =============================================================================
def garantir_modelo():
    from huggingface_hub import hf_hub_download
    
    # Configurações do modelo
    repo_id = "MaziyarPanahi/Llama-3-8B-Instruct-v0.1-GGUF"
    filename = "Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf"
    local_dir = Path("/content/models")
    local_dir.mkdir(exist_ok=True)
    
    model_path = local_dir / filename
    
    if not model_path.exists():
        print(f"📥 [DOWNLOAD] Modelo não detectado. Baixando {filename} do Hugging Face...")
        print("⏳ Isso pode levar alguns minutos (aprox. 4.9 GB)...")
        path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=local_dir
        )
        print(f"✅ [DOWNLOAD] Modelo pronto em: {path}")
        return path
    else:
        print(f"🧠 [CÓRTEX] Modelo detectado em: {model_path}")
        return str(model_path)

# =============================================================================
# 3. NÚCLEO DE INTELIGÊNCIA E TELEGRAM
# =============================================================================
setup_colab() # Executa instalação primeiro
from llama_cpp import Llama
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

# Configurações de Acesso
try:
    from google.colab import userdata
    TOKEN = userdata.get('TELEGRAM_TOKEN')
    print("🔑 [SISTEMA] Token carregado via Colab Secrets.")
except Exception:
    # Caso você esteja rodando fora do Colab ou não configurou a secret
    TOKEN = os.getenv("TELEGRAM_TOKEN") or "COLE_SEU_TOKEN_AQUI_SE_NAO_USAR_SECRETS"

if not TOKEN or "SEU_TOKEN" in TOKEN:
    print("❌ ERRO: Token do Telegram não configurado!")
    sys.exit(1)
AUTHORIZED_USERS = {8117345546, 8379481331}

# Garante o modelo e carrega na GPU
caminho_ia = garantir_modelo()
print("⚡ [VRAM] Alocando modelo na GPU...")
llm = Llama(
    model_path=caminho_ia,
    n_gpu_layers=-1, # -1 usa TODA a GPU disponível
    n_ctx=2048,      # Tamanho da memória de contexto
    verbose=False
)

async def gerar_resposta_ia(prompt):
    """Gera texto usando a GPU do Colab"""
    system_prompt = "Você é o assistente R2, útil, direto e técnico. Responda em Português."
    output = llm(
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n",
        max_tokens=512,
        stop=["<|eot_id|>", "User:"],
        echo=False
    )
    return output['choices'][0]['text'].strip()

async def telegram_handler(update: Update, context):
    uid = update.effective_user.id
    if uid not in AUTHORIZED_USERS: return

    texto = update.message.text
    print(f"📩 [MSG]: {texto}")

    # Filtro simples para comandos de hardware (enviados ao PC local)
    hardware_cmds = ["abrir", "print", "volume", "status", "limpar"]
    if any(c in texto.lower() for c in hardware_cmds):
        await update.message.reply_text("🖥️ *Comando de Hardware detectado.* Processando no terminal local...")
        return

    # Processamento Neural
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        resposta = await gerar_resposta_ia(texto)
        await update.message.reply_text(f"🤖 *R2:* {resposta}", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Erro no Córtex: {e}")

async def run_server():
    print("🛰️ [UPLINK] Servidor R2 ativo no Google Colab.")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_handler))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    # Loop infinito para manter o Colab vivo
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("🛑 Desligando...")