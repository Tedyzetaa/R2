# filename: r2_tactical_os_colab_completo.py
# =================================================================
# R2 TACTICAL OS - Ghost Protocol v8.0 (Google Colab - GPU T4)
# Instalação, download do modelo e execução do servidor com ngrok.
# =================================================================

import os, sys, subprocess, time, threading, json, asyncio, tempfile, base64
from pathlib import Path

# -------------------- 0. FUNÇÃO PARA ESCREVER ARQUIVOS --------------------
def write_file(path, content):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# -------------------- 1. INSTALAÇÃO DE DEPENDÊNCIAS --------------------
print("⚙️ Instalando FFmpeg e bibliotecas...")
subprocess.run("apt-get update -qq && apt-get install ffmpeg -y -qq", shell=True)
subprocess.run("pip install -q fastapi uvicorn websockets edge-tts yt-dlp openai-whisper faiss-cpu sentence-transformers pyngrok nest-asyncio PyPDF2", shell=True)
subprocess.run('CMAKE_ARGS="-DGGML_CUDA=on" pip install -q llama-cpp-python', shell=True)
print("✅ Dependências instaladas.")

# -------------------- 2. BAIXAR MODELO GGUF --------------------
model_dir = Path("/content/models")
model_dir.mkdir(parents=True, exist_ok=True)
model_path = model_dir / "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
if not model_path.exists():
    print("📥 Baixando modelo (2.5 GB) - pode levar alguns minutos...")
    url = "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    subprocess.run(f"wget -q --show-progress {url} -O {model_path}", shell=True)
    print("✅ Modelo baixado.")
else:
    print("✅ Modelo já existe.")

# -------------------- 3. CRIAR BACKEND (main2_colab.py) --------------------
main_backend = '''# filename: main2_colab.py
# (conteúdo completo do backend - será inserido na resposta final)
'''

# -------------------- 4. CRIAR video_ops_colab.py --------------------
video_ops_code = '''# filename: video_ops_colab.py
# (conteúdo completo - será inserido)
'''

# -------------------- 5. CRIAR FRONTEND (index.html, app.js, style.css) --------------------
index_html = '''<!DOCTYPE html>
<html>
... (conteúdo completo)
</html>
'''

app_js = '''/* filename: static/js/app.js */
// (código original do usuário)
'''

style_css = '''/* filename: static/css/style.css */
// (código original do usuário)
'''

# Escrever os arquivos
write_file("/content/main2_colab.py", main_backend)
write_file("/content/video_ops_colab.py", video_ops_code)
write_file("/content/static/index.html", index_html)
write_file("/content/static/js/app.js", app_js)
write_file("/content/static/css/style.css", style_css)
print("✅ Arquivos do sistema criados.")

# -------------------- 6. INICIAR SERVIDOR EM BACKGROUND --------------------
def start_server():
    os.system("python /content/main2_colab.py")

threading.Thread(target=start_server, daemon=True).start()
print("🚀 Servidor FastAPI iniciado em background.")

# Aguardar ngrok
time.sleep(6)
try:
    from pyngrok import ngrok
    tunnels = ngrok.get_tunnels()
    if tunnels:
        url = tunnels[0].public_url
        print(f"\n🔗 **R2 Tactical OS online** → {url}")
        print(f"🎤 WebSocket: {url.replace('https', 'wss')}/ws")
    else:
        print("⚠️ Nenhum túnel ngrok. Configure seu authtoken: conf.get_default().auth_token = 'SEU_TOKEN'")
except Exception as e:
    print(f"⚠️ Erro ao obter URL: {e}")

print("\n✅ Sistema pronto. Pressione Ctrl+C para interromper (ou interrompa a célula).")
while True:
    time.sleep(10)