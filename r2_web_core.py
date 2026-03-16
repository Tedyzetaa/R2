import subprocess
import sys
import os

# ==========================================
# 📦 PROTOCOLO DE AUTO-INSTALAÇÃO (BOOT)
# ==========================================
def check_dependencies():
    print("🛰️ [SISTEMA]: Verificando integridade das dependências...")
    deps = [
        "psutil", "python-dotenv", "requests", "diffusers", 
        "transformers", "accelerate", "peft", "torch", "torchvision",
        "llama-cpp-python", "fastapi", "uvicorn", "websockets", 
        "python-multipart", "beautifulsoup4", "geopy", "matplotlib"
    ]
    for dep in deps:
        try:
            # Algumas bibliotecas têm nomes de import diferentes do nome do pip
            import_name = dep.replace("-", "_")
            if dep == "beautifulsoup4": import_name = "bs4"
            __import__(import_name)
        except ImportError:
            print(f"📥 Instalando dependência faltante: {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--quiet"])
    print("✅ [SISTEMA]: Todas as dependências estão operacionais.")

# Executa a verificação antes de importar o resto
check_dependencies()

# Agora os imports pesados podem acontecer com segurança
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
# Certifique-se de que este caminho existe no seu Repo
MODEL_PATH = "models/dolphin-2.9-llama3-8b.Q4_K_M.gguf"

if not os.path.exists(MODEL_PATH):
    print(f"⚠️ [AVISO]: Modelo não encontrado em {MODEL_PATH}")
    # Aqui você poderia adicionar um código de download automático se desejar

CEREBRO = Llama(
    model_path=MODEL_PATH,
    n_ctx=4096,
    n_gpu_layers=-1, 
    verbose=False
)

print("🎨 Inicializando Motor Visual...")
MOTOR_VISUAL = ImageGenerator()

# ==========================================
# 🌐 CONFIGURAÇÃO DO SERVIDOR WEB (FASTAPI)
# ==========================================
app = FastAPI(title="R2 Web Core")

# Cria as pastas necessárias
os.makedirs("static/renders", exist_ok=True)

# Monta a pasta estática
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

class ImageRequest(BaseModel):
    prompt: str

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
            mensagem_usuario = await websocket.receive_text()
            
            prompt_formatado = f"<|im_start|>system\nVocê é o R2, uma IA tática de alta precisão.<|im_end|>\n"
            for m in historico[-5:]:
                prompt_formatado += f"<|im_start|>user\n{m['user']}<|im_end|>\n<|im_start|>assistant\n{m['bot']}<|im_end|>\n"
            
            prompt_formatado += f"<|im_start|>user\n{mensagem_usuario}<|im_end|>\n<|im_start|>assistant\n"

            stream = CEREBRO(
                prompt_formatado,
                max_tokens=1024,
                stop=["<|im_end|>", "<|im_start|>"],
                stream=True
            )
            
            resposta_completa = ""
            for chunk in stream:
                texto_chunk = chunk["choices"][0]["text"]
                resposta_completa += texto_chunk
                await websocket.send_text(texto_chunk)
            
            await websocket.send_text("[DONE]")
            historico.append({"user": mensagem_usuario, "bot": resposta_completa})

    except WebSocketDisconnect:
        print("⚠️ Conexão do terminal web encerrada.")

@app.post("/api/image")
async def generate_image(req: ImageRequest):
    try:
        if not MOTOR_VISUAL.pipe:
            MOTOR_VISUAL.load_engine()
        
        # Chama a função do seu image_gen.py
        # Nota: Ajustei para o padrão da diffusers (images[0])
        result = MOTOR_VISUAL.pipe(req.prompt).images[0]
        
        nome_arquivo = f"render_{int(time.time())}.png"
        caminho_salvar = os.path.join("static", "renders", nome_arquivo)
        
        result.save(caminho_salvar)
        
        return {"status": "success", "image_url": f"/static/renders/{nome_arquivo}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    print("🚀 [R2]: Servidor Web Iniciado.")
    # No Colab, use a porta 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)