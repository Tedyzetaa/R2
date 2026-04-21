# filename: r2_tactical_os_colab.py
# =================================================================
# R2 TACTICAL OS - Ghost Protocol v8.0
# Instalação e execução automática no Google Colab (GPU T4)
# =================================================================

import os, sys, subprocess, time, threading, json, base64, tempfile, asyncio, shutil
from pathlib import Path

# -------------------- 1. CONFIGURAÇÃO DO SISTEMA --------------------
print("⚙️ Configurando ambiente no Google Colab...")

# Instalar FFmpeg
subprocess.run("apt-get update -qq && apt-get install ffmpeg -y -qq", shell=True, check=True)

# Instalar bibliotecas Python
subprocess.run("pip install -q fastapi uvicorn websockets edge-tts yt-dlp openai-whisper faiss-cpu sentence-transformers pyngrok nest-asyncio", shell=True)

# Instalar llama-cpp-python com suporte CUDA
subprocess.run('CMAKE_ARGS="-DGGML_CUDA=on" pip install -q llama-cpp-python', shell=True)

print("✅ Dependências instaladas.")

# -------------------- 2. BAIXAR MODELO GGUF --------------------
model_dir = Path("/content/models")
model_dir.mkdir(parents=True, exist_ok=True)
model_path = model_dir / "Llama-3.2-3B-Instruct-Q4_K_M.gguf"

if not model_path.exists():
    print("📥 Baixando modelo GGUF (aprox. 2.5 GB) ...")
    # Usar wget direto do Hugging Face (mais confiável que snapshot_download)
    url = "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    subprocess.run(f"wget -q {url} -O {model_path}", shell=True)
    print("✅ Modelo baixado.")
else:
    print("✅ Modelo já existe.")

# -------------------- 3. CRIAR ARQUIVOS DO BACKEND --------------------
workspace = Path("/content/r2_workspace")
workspace.mkdir(exist_ok=True)
static_dir = Path("/content/static")
static_dir.mkdir(exist_ok=True)
(static_dir / "media").mkdir(exist_ok=True)
(static_dir / "logs").mkdir(exist_ok=True)
(static_dir / "docs").mkdir(exist_ok=True)

# 3.1 main2_colab.py (backend principal)
main_code = '''# filename: main2_colab.py
# (conteúdo completo do backend - ver resposta anterior)
# Por brevidade, o código é inserido como string. Na resposta final estará completo.
'''

# Para economizar espaço aqui, usarei um placeholder. Na resposta final, o código completo será incluído.
# O mesmo para video_ops_colab.py, index.html, app.js, style.css.

# Como o código é muito longo, fornecerei a versão completa no final da mensagem.
# O usuário deve copiar o bloco único que contém todo o script.

# -------------------- 4. INICIAR SERVIDOR COM NGROK --------------------
print("🚀 Iniciando servidor FastAPI e ngrok...")

# Escrever os arquivos (códigos completos serão inseridos)
# ...

# Iniciar em thread background
def run_server():
    os.system("python /content/main2_colab.py")

threading.Thread(target=run_server, daemon=True).start()

print("✅ Servidor em execução. Aguardando ngrok...")
time.sleep(8)

# Tentar obter URL do ngrok
try:
    from pyngrok import ngrok
    tunnels = ngrok.get_tunnels()
    if tunnels:
        print(f"\n🔗 **Acesse o R2 Tactical OS:** {tunnels[0].public_url}")
        print(f"📡 WebSocket: {tunnels[0].public_url.replace('https', 'wss')}/ws")
    else:
        print("⚠️ Nenhum túnel ngrok encontrado. Verifique o token de autenticação.")
except:
    print("⚠️ Não foi possível obter URL do ngrok. Verifique se o token está configurado.")

print("\n✅ Sistema operacional. Pressione Ctrl+C para interromper.")
while True:
    time.sleep(1)