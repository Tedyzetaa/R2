import os
import sys
import platform
from llama_cpp import Llama

# ==========================================
# 1. CONFIGURAÇÕES E PATHS
# ==========================================
IS_WINDOWS = platform.system() == "Windows"
TOKEN = sys.argv[1] if len(sys.argv) > 1 else "SEU_TOKEN_AQUI"

# Configuração que você pegou no site
REPO_ID = "markhneedham/dolphin-2.9-llama3-8b-Q4_K_M-GGUF"
MODEL_FILE = "dolphin-2.9-llama3-8b-q4_k_m.gguf" # Nome sugerido pelo site

# ==========================================
# 2. INICIALIZAÇÃO DA IA (MÉTODO DO SITE)
# ==========================================
print(f"--- R2 INICIANDO (MODO: {'WINDOWS' if IS_WINDOWS else 'COLAB'}) ---")
print(f"--- Carregando modelo do repositório: {REPO_ID} ---")

try:
    # Usando o método que você encontrou no site
    llm = Llama.from_pretrained(
        repo_id=REPO_ID,
        filename=MODEL_FILE,
        n_ctx=2048,
        n_gpu_layers=-1 if not IS_WINDOWS else 0 # No Windows use 0 se não tiver CUDA configurado
    )
except Exception as e:
    print(f"❌ Erro ao carregar: {e}")
    print("Tentando alternativa com nome de arquivo corrigido...")
    # Plano B: Caso o nome em minúsculas falhe, tentamos o padrão CamelCase
    llm = Llama.from_pretrained(
        repo_id=REPO_ID,
        filename="Dolphin-2.9-Llama-3-8B-Q4_K_M.gguf",
        n_ctx=2048
    )

# ==========================================
# 3. INTERFACE DO TELEGRAM
# ==========================================
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id

    # COMANDO DE IMAGEM
    if user_text.lower().startswith("/imagem "):
        prompt = user_text[8:]
        await update.message.reply_text("🎨 Gerando imagem via Stable Diffusion...")
        # (Aqui entra a lógica do diffusers que configuramos antes)
        return

    # COMANDOS TÁTICOS (RADAR)
    if user_text.lower().startswith("radar"):
        await update.message.reply_chat_action("typing")
        from features.air_traffic import AirTrafficControl
        radar = AirTrafficControl()
        filename, qtd, msg = radar.radar_scan(user_text[5:].strip() or "Ivinhema")
        if filename and os.path.exists(filename):
            with open(filename, 'rb') as f:
                await context.bot.send_photo(chat_id=chat_id, photo=f, caption=msg)
        return

    # CONVERSA PADRÃO
    await update.message.reply_chat_action("typing")
    output = llm(
        f"<|im_start|>user\n{user_text}<|im_end|>\n<|im_start|>assistant\n",
        max_tokens=512,
        stop=["<|im_end|>"]
    )
    await update.message.reply_text(output['choices'][0]['text'])

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("--- R2 ONLINE ---")
    app.run_polling()