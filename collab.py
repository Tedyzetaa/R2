import os
import sys
import subprocess
import asyncio
from pathlib import Path

# =============================================================================
# 1. AUTO-CONFIGURAÇÃO (GPU + DEPENDÊNCIAS)
# =============================================================================
def setup_colab():
    print("🚀 [SISTEMA] Iniciando Protocolos de Dependência...")
    
    # Tenta instalar a versão pré-compilada para evitar erro de 'Building Wheel'
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "llama-cpp-python", 
            "--extra-index-url", "https://abetlen.github.io/llama-cpp-python/whl/cu121",
            "--quiet"
        ])
    except:
        print("⚠️ Falha na instalação rápida, tentando modo de compilação...")
        os.environ["FORCE_CMAKE"] = "1"
        os.environ["CMAKE_ARGS"] = "-DLLAMA_CUBLAS=on"
        subprocess.check_call([sys.executable, "-m", "pip", "install", "llama-cpp-python", "--quiet"])

    # Instala o restante das dependências
    deps = ["python-dotenv", "python-telegram-bot", "requests", "huggingface_hub"]
    for dep in deps:
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--quiet"])
    
    print("✅ [SISTEMA] Ambiente configurado.")

# Executa o setup antes de importar os módulos pesados
setup_colab()

from llama_cpp import Llama
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

# =============================================================================
# 2. BUSCA AUTOMÁTICA DO TOKEN (COLAB SECRETS)
# =============================================================================
try:
    from google.colab import userdata
    TOKEN = userdata.get('TELEGRAM_TOKEN')
    print("🔑 [SISTEMA] Token recuperado via Google Secrets.")
except Exception:
    # Se não estiver no Colab ou a secret não existir, tenta ler do ambiente ou manual
    TOKEN = os.getenv("TELEGRAM_TOKEN") or "SEU_TOKEN_AQUI"

# IDs autorizados (Teddy e secundários)
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
        print(f"📥 [DOWNLOAD] Baixando Llama-3 (4.9 GB)...")
        path = hf_hub_download(repo_id=repo_id, filename=filename, local_dir=local_dir)
        return path
    return str(model_path)

# Carregamento do Córtex Neural
caminho_ia = garantir_modelo()
print("🧠 [CÓRTEX] Alocando modelo na GPU T4...")
llm = Llama(model_path=caminho_ia, n_gpu_layers=-1, n_ctx=2048, verbose=False)

# =============================================================================
# 4. PROCESSAMENTO E RESPOSTA
# =============================================================================
async def gerar_ia(prompt):
    system_prompt = "Você é o R2, um assistente técnico avançado. Responda de forma curta e precisa."
    output = llm(
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n",
        max_tokens=256, stop=["<|eot_id|>"], echo=False
    )
    return output['choices'][0]['text'].strip()

async def handler(update: Update, context):
    if update.effective_user.id not in AUTHORIZED_USERS: return
    
    texto = update.message.text
    print(f"📥 [R2]: {texto}")

    # Filtro para o PC Local executar (se houver palavras de comando físico)
    físico = ["abrir", "print", "screenshot", "volume", "desligar"]
    if any(cmd in texto.lower() for cmd in físico):
        await update.message.reply_text("🖥️ *Comando Físico Detectado:* Aguardando execução no terminal local.")
        return

    # Processamento por IA
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        resposta = await gerar_ia(texto)
        await update.message.reply_text(f"🤖 *R2:* {resposta}", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Erro: {e}")

async def main():
    if not TOKEN or "SEU_TOKEN" in TOKEN:
        print("❌ [ERRO] TOKEN NÃO ENCONTRADO! Verifique as Secrets (ícone da chave 🔑).")
        return

    print("🛰️ [UPLINK] Servidor R2 Online e ouvindo...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Sistema encerrado.")