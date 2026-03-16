import subprocess
import sys
import os
import requests

# ==========================================
# 📦 CONFIGURAÇÃO DE DIRETÓRIOS E LINKS
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
LORA_DIR = os.path.join(MODELS_DIR, "loras")
CHECKPOINT_DIR = os.path.join(MODELS_DIR, "checkpoints")

# Mapeamento de Modelos (Nome: (URL, Caminho Local))
MODEL_MAP = {
    "Dolphin LLM": (
        "https://huggingface.co/MaziyarPanahi/dolphin-2.9-llama3-8b-GGUF/resolve/main/dolphin-2.9-llama3-8b.Q4_K_M.gguf",
        os.path.join(MODELS_DIR, "dolphin-2.9-llama3-8b.Q4_K_M.gguf")
    ),
    "Realistic Vision Checkpoint": (
        "https://civitai.com/api/download/models/501286",
        os.path.join(CHECKPOINT_DIR, "v1-5-pruned.safetensors")
    ),
    "Detailed Perfection LoRA": (
        "https://civitai.com/api/download/models/459068",
        os.path.join(LORA_DIR, "detailed_perfection.safetensors")
    ),
    "Realistic Skin LoRA": (
        "https://civitai.com/api/download/models/648753",
        os.path.join(LORA_DIR, "realistic_skin.safetensors")
    ),
    "Amateur Photography LoRA": (
        "https://civitai.com/api/download/models/730302",
        os.path.join(LORA_DIR, "amateur_photography.safetensors")
    )
}

# ==========================================
# 📥 FUNÇÃO DE DOWNLOAD E DEPENDÊNCIAS
# ==========================================
def download_file(url, destination):
    if os.path.exists(destination):
        return
    
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    print(f"📥 Baixando: {os.path.basename(destination)}...")
    
    # Usando streaming para não estourar a RAM no download
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        downloaded = 0
        with open(destination, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    done = int(50 * downloaded / total_size)
                    sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded/(1024*1024):.1f}MB")
                    sys.stdout.flush()
    print(f"\n✅ Concluído.")

def boot_system():
    print("🛰️ [SISTEMA]: Verificando integridade...")
    
    # 1. Instala Bibliotecas
    deps = ["psutil", "python-dotenv", "requests", "diffusers", "transformers", 
            "accelerate", "peft", "torch", "torchvision", "llama-cpp-python", 
            "fastapi", "uvicorn", "websockets", "python-multipart"]
    for dep in deps:
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--quiet"])
    
    # 2. Baixa Modelos
    for name, (url, path) in MODEL_MAP.items():
        download_file(url, path)

boot_system()

# ==========================================
# 📂 CONFIGURAÇÃO DE IMPORTS E PATHS
# ==========================================
FEATURES_PATH = os.path.join(BASE_DIR, "features")
if FEATURES_PATH not in sys.path:
    sys.path.insert(0, FEATURES_PATH)

import asyncio
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from llama_cpp import Llama
from image_gen import ImageGenerator

# ==========================================
# 🧠 INICIALIZAÇÃO DE MOTORES
# ==========================================
print("🧠 Inicializando Cérebro Dolphin...")
CEREBRO = Llama(
    model_path=MODEL_MAP["Dolphin LLM"][1],
    n_ctx=4096,
    n_gpu_layers=-1, # Ativa aceleração por GPU no Colab
    verbose=False
)

print("🎨 Inicializando Motor Visual...")
MOTOR_VISUAL = ImageGenerator()

app = FastAPI()
os.makedirs("static/renders", exist_ok=True)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Erro: static/index.html não encontrado.</h1>"

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    historico = []
    try:
        while True:
            msg = await websocket.receive_text()
            prompt = f"<|im_start|>system\nVocê é o R2.<|im_end|>\n"
            for m in historico[-3:]:
                prompt += f"<|im_start|>user\n{m['u']}<|im_end|>\n<|im_start|>assistant\n{m['b']}<|im_end|>\n"
            prompt += f"<|im_start|>user\n{msg}<|im_end|>\n<|im_start|>assistant\n"

            stream = CEREBRO(prompt, max_tokens=512, stop=["<|im_end|>"], stream=True)
            resp_full = ""
            for chunk in stream:
                token = chunk["choices"][0]["text"]
                resp_full += token
                await websocket.send_text(token)
            await websocket.send_text("[DONE]")
            historico.append({"u": msg, "b": resp_full})
    except WebSocketDisconnect:
        pass

@app.post("/api/image")
async def generate_image(req: BaseModel):
    # Lógica de geração simplificada para o exemplo
    pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)