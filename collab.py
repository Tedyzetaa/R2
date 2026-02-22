import os
import sys
import subprocess
import asyncio
from pathlib import Path

# =============================================================================
# 1. CORREÇÃO DE DIRETÓRIO E AMBIENTE
# =============================================================================
# Garante que o script rode na pasta correta, não importa quantas vezes foi clonado
if '/content/R2' in os.getcwd():
    os.chdir('/content/R2')

def setup_colab():
    print("🚀 [SISTEMA] Iniciando Protocolos de Dependência...")
    
    # Instalação rápida do Llama-CPP para GPU T4
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "llama-cpp-python", 
            "--extra-index-url", "https://abetlen.github.io/llama-cpp-python/whl/cu121",
            "--quiet"
        ])
    except:
        print("⚠️ Build manual necessário...")
        os.environ["FORCE_CMAKE"] = "1"
        os.environ["CMAKE_ARGS"] = "-DLLAMA_CUBLAS=on"
        subprocess.check_call([sys.executable, "-m", "pip", "install", "llama-cpp-python", "--quiet"])

    deps = ["python-dotenv", "python-telegram-bot", "requests", "huggingface_hub"]
    for dep in deps:
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--quiet"])
    print("✅ [SISTEMA] Ambiente configurado.")

# Inicia dependências
setup_colab()

from llama_cpp import Llama
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from telegram.request import HTTPXRequest

# =============================================================================
# 2. VERIFICAÇÃO DINÂMICA DO TOKEN (INTEGRADO)
# =============================================================================
def obter_token_seguro():
    # 1. Tenta ler a variável de ambiente (injetada pela célula do Colab)
    token = os.environ.get('TELEGRAM_TOKEN')
    
    if token and "SEU_TOKEN" not in token:
        return token
        
    # 2. Se falhar, tenta o método direto (apenas se rodar a célula direto)
    try:
        from google.colab import userdata
        return userdata.get('TELEGRAM_TOKEN')
    except:
        return None

TOKEN = obter_token_seguro()
AUTHORIZED_USERS = {8117345546, 8379481331}

# =============================================================================
# 3. GESTÃO DO MODELO IA
# =============================================================================
def garantir_modelo():
    from huggingface_hub import hf_hub_download
    repo_id = "MaziyarPanahi/Llama-3-8B-Instruct-v0.1-GGUF"
    filename = "Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf"
    local_dir = Path("/content/models")
    local_dir.mkdir(exist_ok=True)
    
    model_path = local_dir / filename
    if not model_path.exists():
        print(f"📥 [DOWNLOAD] Baixando Llama-3 (5GB)...")
        return hf_hub_download(repo_id=repo_id, filename=filename, local_dir=local_dir)
    print(f"🧠 [CÓRTEX] Modelo detectado.")
    return str(model_path)

caminho_ia = garantir_modelo()
llm = Llama(model_path=caminho_ia, n_gpu_layers=-1, n_ctx=2048, verbose=False)

# =============================================================================
# 4. HANDLERS E EXECUÇÃO
# =============================================================================
async def gerar_ia(prompt):
    # Removido o <|begin_of_text|> do início
    template = f"<|start_header_id|>system<|end_header_id|>\n\nVocê é o R2.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    output = llm(template, max_tokens=256, stop=["<|eot_id|>"], echo=False)
    return output['choices'][0]['text'].strip()

async def handler(update: Update, context):
    if update.effective_user.id not in AUTHORIZED_USERS: return
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        resposta = await gerar_ia(update.message.text)
        await update.message.reply_text(f"🤖 *R2:* {resposta}", parse_mode='Markdown')
    except Exception as e:
        print(f"Erro: {e}")

async def main():
    if not TOKEN or "SEU_TOKEN" in TOKEN:
        print("\n❌ [ERRO CRÍTICO]: TOKEN NÃO ENCONTRADO!")
        print("Certifique-se de:")
        print("1. Clicar no ícone da CHAVE 🔑 à esquerda.")
        print("2. Adicionar 'TELEGRAM_TOKEN' com seu token.")
        print("3. Ativar o botão 'Notebook access'.\n")
        return

    # Criamos um objeto de requisição com timeouts maiores (30 seg)
    t_request = HTTPXRequest(connect_timeout=30, read_timeout=30)
    
    print("🛰️ [UPLINK] Servidor R2 Online no Colab.")
    # Passamos o request_kwargs para a aplicação
    app = Application.builder().token(TOKEN).request(t_request).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    await app.initialize()
    await app.start()
    # O polling também precisa de tolerância
    await app.updater.start_polling(drop_pending_updates=True, read_timeout=30)
    while True: await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass