import os
import time
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from llama_cpp import Llama

# Importa o teu módulo atual de imagem
from features.image_gen import ImageGenerator

# ==========================================
# 🧠 INICIALIZAÇÃO DE MOTORES
# ==========================================
print("🧠 Iniciando Cérebro Dolphin...")
CEREBRO = Llama(
    model_path="models/dolphin-2.9-llama3-8b-Q4_K_M.gguf", # <-- Path corrigido
    n_ctx=4096,
    n_gpu_layers=-1, 
    verbose=False
)

print("🎨 Iniciando Motor Visual...")
MOTOR_VISUAL = ImageGenerator()

# ==========================================
# 🌐 CONFIGURAÇÃO DO SERVIDOR WEB (FASTAPI)
# ==========================================
app = FastAPI(title="R2 Web Core")

# Cria as pastas necessárias
os.makedirs("static", exist_ok=True)
os.makedirs("static/renders", exist_ok=True)

# Monta a pasta estática para servir imagens e o HTML
app.mount("/static", StaticFiles(directory="static"), name="static")

# Estrutura de dados para a API de imagem
class ImageRequest(BaseModel):
    prompt: str

# 1. ROTA PRINCIPAL: Serve a Interface HTML
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# 2. ROTA DE TEXTO: WebSocket para Streaming em tempo real
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    historico = [] # Memória temporária da sessão
    
    try:
        while True:
            mensagem_usuario = await websocket.receive_text()
            
            # Formatação do prompt para o Dolphin (Llama 3 format)
            prompt_formatado = "<|im_start|>system\nVocê é o R2, uma IA tática de alta precisão.<|im_end|>\n"
            for m in historico[-5:]: # Lembra as últimas 5 mensagens
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
                # Envia pedaço por pedaço para a interface web
                await websocket.send_text(texto_chunk)
                await asyncio.sleep(0.01) # Pequeno respiro para a thread
            
            # Sinaliza que terminou de gerar
            await websocket.send_text("[DONE]")
            
            historico.append({"user": mensagem_usuario, "bot": resposta_completa})

    except WebSocketDisconnect:
        print("⚠️ Conexão do terminal web encerrada.")

# 3. ROTA DE IMAGEM: Gera imagem via POST e devolve a URL
@app.post("/api/image")
async def generate_image(req: ImageRequest):
    try:
        if not MOTOR_VISUAL.pipe:
            MOTOR_VISUAL.load_engine()
        
        # Gera a imagem (ajusta de acordo com o retorno do teu image_gen.py)
        imagem_gerada = MOTOR_VISUAL.pipe(req.prompt).images[0]
        
        nome_arquivo = f"render_{int(time.time())}.png"
        caminho_salvar = f"static/renders/{nome_arquivo}"
        
        imagem_gerada.save(caminho_salvar)
        
        return {"status": "success", "image_url": f"/static/renders/{nome_arquivo}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ==========================================
# 🚀 INICIALIZAÇÃO
# ==========================================
if __name__ == "__main__":
    print("🌐 [UPLINK]: Servidor Web Iniciado na porta 8000")
    print("➡️  Acesse: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)