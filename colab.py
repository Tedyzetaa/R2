import os
import sys
import subprocess
import time
import asyncio
import threading
import requests
import re
import base64
import gc
import shutil
from io import BytesIO
from PIL import Image
import numpy as np

# ==========================================
# 🛠️ 1. MOTOR DE AUTO-INSTALAÇÃO (BOOTSTRAP)
# ==========================================
def garantir_ambiente():
    print("\n" + "="*50)
    print("⚙️ [BOOTSTRAP] PREPARANDO AMBIENTE SUPREMO")
    print("="*50)
    
    # Lista de dependências de alto calibre
    deps = [
        "fastapi", "uvicorn", "websockets", "python-multipart", 
        "huggingface_hub", "requests", "psutil", "python-dotenv", 
        "llama-cpp-python", "greenlet", "playwright", "speedtest-cli",
        "feedparser", "geopy", "matplotlib", "beautifulsoup4",
        "diffusers", "transformers", "accelerate", "torch", "peft", "adetailer",
        "PyPDF2", "sentence-transformers", "faiss-cpu", "numpy<2", "pyngrok"
    ]
    
    for package in deps:
        try:
            name = package.split('<')[0] if '<' in package else package
            __import__(name.replace("-", "_").replace("python-dotenv", "dotenv").replace("opencv-python", "cv2"))
        except ImportError:
            print(f"📦 Instalando componente: {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])

# Executa o bootstrap antes de qualquer importação especial
garantir_ambiente()

# ==========================================
# 📂 2. IMPORTAÇÕES PÓS-INSTALAÇÃO
# ==========================================
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pyngrok import ngrok 
import torch
from diffusers import StableDiffusionPipeline, EulerAncestralDiscreteScheduler
from transformers import CLIPVisionModelWithProjection

# ==========================================
# 🔑 CONFIGURAÇÃO DO NGROK
# ==========================================
NGROK_TOKEN = "COLE_SEU_TOKEN_DO_NGROK_AQUI"

# Desativa avisos de Administrador
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

# ==========================================
# 📂 3. GESTOR DE MÓDULOS (PASTA FEATURES)
# ==========================================
def safe_import(module_name, class_name):
    try:
        import importlib
        mod = importlib.import_module(f"features.{module_name}")
        return getattr(mod, class_name)
    except Exception as e:
        print(f"⚠️ Alerta: Módulo {class_name} ({module_name}) indisponível: {e}")
        return None

# Importação do Arsenal
OrbitalSystem = safe_import("orbital_system", "OrbitalSystem")
RadarAereoAPI = safe_import("radar_api", "RadarAereoAPI")
AstroDefenseSystem = safe_import("astro_defense", "AstroDefenseSystem")
PizzaINTService = safe_import("pizzint_service", "PizzaINTService")
NOAAService = safe_import("noaa_service", "NOAAService")
GeoSeismicSystem = safe_import("geo_seismic", "GeoSeismicSystem")
SpeedTestModule = safe_import("net_speed", "SpeedTestModule")
SentinelSystem = safe_import("sentinel_system", "SentinelSystem")
MarketSystem = safe_import("market_system", "MarketSystem")
NewsBriefing = safe_import("news_briefing", "NewsBriefing")

# ==========================================
# 📚 4. NÚCLEO RAG (PROCESSADOR DE PDFs)
# ==========================================
class KnowledgeBase:
    def __init__(self, docs_dir="static/docs"):
        self.docs_dir = docs_dir
        self.embedder = None
        self.index = None
        self.chunks = []
        os.makedirs(self.docs_dir, exist_ok=True)

    def sync(self):
        import faiss
        import PyPDF2
        from sentence_transformers import SentenceTransformer
        if not self.embedder: 
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.chunks = []
        pdf_files = [f for f in os.listdir(self.docs_dir) if f.lower().endswith('.pdf')]
        if not pdf_files: return "⚠️ Nenhum PDF encontrado em static/docs."
        
        for pdf_file in pdf_files:
            try:
                with open(os.path.join(self.docs_dir, pdf_file), 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = "".join([p.extract_text() or "" for p in reader.pages])
                    for i in range(0, len(text), 800):
                        chunk = text[i:i+1000].strip()
                        if len(chunk) > 50: self.chunks.append(f"[Fonte: {pdf_file}] {chunk}")
            except: continue
        
        if not self.chunks: return "⚠️ Falha ao ler PDFs (podem estar corrompidos ou protegidos)."
        embeddings = self.embedder.encode(self.chunks, convert_to_numpy=True)
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)
        return f"✅ Cérebro Atualizado! {len(pdf_files)} arquivos integrados à base."

    def search(self, query):
        if not self.index: return None
        q_emb = self.embedder.encode([query], convert_to_numpy=True)
        _, indices = self.index.search(q_emb, 3)
        return "\n\n".join([self.chunks[idx] for idx in indices[0] if idx < len(self.chunks)])

# ==========================================
# 🎨 5. MOTOR VISUAL (UNFILTERED v2.1)
# ==========================================
class UltraVisualCore:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = None
        self.model_id = "UnfilteredAI/NSFW-gen-v2.1"
        
    def load_engine(self):
        if self.pipe: return
        print(f"\n🎨 [VISUAL]: Inicializando Motor Unfiltered v2.1...")
        self.pipe = StableDiffusionPipeline.from_pretrained(
            self.model_id, 
            torch_dtype=torch.float16,
            safety_checker=None,
            requires_safety_checker=False
        )
        self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(self.pipe.scheduler.config)
        if self.device == "cuda":
            self.pipe.enable_model_cpu_offload()
        print("✅ Motor visual operacional.")

    def generate(self, prompt):
        if not self.pipe: self.load_engine()
        gc.collect()
        if torch.cuda.is_available(): torch.cuda.empty_cache()
        
        positive = f"photo of {prompt}, ultra detailed, realistic skin, 8k, raw"
        with torch.inference_mode(), torch.autocast(self.device):
            # Resolução ideal para SD 1.5
            image = self.pipe(positive, num_inference_steps=30, height=768, width=512, guidance_scale=7.5).images[0]
        return image

# ==========================================
# 🧠 6. INICIALIZAÇÃO DE SISTEMAS
# ==========================================
os.makedirs("static/media", exist_ok=True)
rag_ops = KnowledgeBase()
img_ops = UltraVisualCore()
iss_ops = OrbitalSystem() if OrbitalSystem else None
radar_ops = RadarAereoAPI() if RadarAereoAPI else None
astro_ops = AstroDefenseSystem() if AstroDefenseSystem else None
pizza_ops = PizzaINTService(config={}) if PizzaINTService else None
noaa_ops = NOAAService() if NOAAService else None
sismo_ops = GeoSeismicSystem() if GeoSeismicSystem else None
speed_ops = SpeedTestModule() if SpeedTestModule else None
sentinel_ops = SentinelSystem() if SentinelSystem else None
market_ops = MarketSystem() if MarketSystem else None
news_ops = NewsBriefing() if NewsBriefing else None

try:
    from llama_cpp import Llama
    ai_brain = Llama(model_path="models/Dolphin3.0-Llama3.1-8B-Q4_K_M.gguf", n_ctx=16384, n_gpu_layers=10, verbose=False)
except: ai_brain = None

# ==========================================
# 🌐 7. SERVIDOR WEB E INTERFACE (MENU KEBAB)
# ==========================================
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>R2 TACTICAL OS</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
    <style>
        :root { --bg: #050510; --neon: #00ffff; --panel: rgba(10, 10, 26, 0.95); --bot-bg: rgba(0, 26, 0, 0.4); }
        body { background: var(--bg); color: #e0e0e0; font-family: 'Segoe UI', sans-serif; margin: 0; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
        #header { background: var(--panel); padding: 15px 25px; border-bottom: 1px solid rgba(0,255,255,0.2); display: flex; justify-content: space-between; align-items: center; }
        .kebab { cursor: pointer; padding: 10px; font-size: 24px; color: var(--neon); font-weight: bold; }
        #tactical-panel { position: absolute; top: 60px; right: 20px; background: var(--panel); border: 1px solid var(--neon); border-radius: 8px; width: 280px; display: none; flex-direction: column; padding: 10px; z-index: 1000; box-shadow: 0 0 30px rgba(0,0,0,0.8); }
        #tactical-panel.show { display: flex; }
        .btn { background: rgba(255,255,255,0.05); border: 1px solid #333; color: #fff; padding: 10px; margin: 3px 0; border-radius: 4px; cursor: pointer; text-align: left; font-size: 12px; }
        .btn:hover { background: var(--neon); color: #000; font-weight: bold; }
        #chat-wrapper { flex: 1; overflow-y: auto; padding: 25px; display: flex; flex-direction: column; gap: 20px; }
        .msg { max-width: 85%; padding: 15px; border-radius: 12px; line-height: 1.6; font-size: 15px; }
        .user-msg { align-self: flex-end; background: rgba(0,255,255,0.1); border: 1px solid var(--neon); }
        .r2-msg { align-self: flex-start; background: var(--bot-bg); border: 1px solid #00ff00; width: 95%; }
        img { max-width: 100%; border-radius: 8px; border: 1px solid #00ff00; margin-top: 10px; }
        #input-area { padding: 20px; background: var(--panel); display: flex; gap: 10px; border-top: 1px solid #333; }
        textarea { flex: 1; background: #000; color: #fff; border: 1px solid #004444; border-radius: 6px; padding: 12px; resize: none; outline: none; }
        .send { background: #006666; color: #fff; border: none; padding: 0 25px; border-radius: 6px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div id="header">
        <h2 style="color:var(--neon); margin:0; letter-spacing:2px;">⚡ R2 TACTICAL OS</h2>
        <div class="kebab" onclick="toggleMenu()">⋮</div>
        <div id="tactical-panel">
            <button class="btn" style="color:gold; border-color:gold;" onclick="exec('/doc sync')">🧠 SINCRONIZAR PDFs</button>
            <button class="btn" onclick="exec('/cmd radar')">📡 RADAR AÉREO</button>
            <button class="btn" onclick="exec('/cmd iss')">🛰️ RASTREAR ISS</button>
            <button class="btn" onclick="exec('/cmd solar')">☀️ MONITOR SOLAR (NOAA)</button>
            <button class="btn" onclick="exec('/cmd astro')">☄️ DEFESA PLANETÁRIA</button>
            <button class="btn" onclick="exec('/cmd pizza')">🍕 MONITOR PIZZINT</button>
            <button class="btn" onclick="exec('/cmd market')">💰 MERCADO FINANCEIRO</button>
            <button class="btn" onclick="exec('/cmd sismo')">🌍 MONITOR SÍSMICO</button>
            <button class="btn" onclick="exec('/cmd net')">⚡ SPEEDTEST REDE</button>
            <button class="btn" onclick="exec('/cmd sentinel')">👁️ ATIVAR SENTINELA</button>
        </div>
    </div>
    <div id="chat-wrapper"><div id="chat"></div></div>
    <div id="input-area">
        <textarea id="msgBox" rows="1" placeholder="Diga: /img [prompt] ou fale com R2..."></textarea>
        <button class="send" onclick="send()">ENVIAR</button>
    </div>
    <script>
        const ws = new WebSocket("ws://" + window.location.host + "/ws");
        const chat = document.getElementById("chat");
        const chatWrap = document.getElementById("chat-wrapper");
        function toggleMenu() { document.getElementById("tactical-panel").classList.toggle("show"); }
        function exec(c) { ws.send(c); toggleMenu(); addMsg(c, 'user-msg'); }
        ws.onmessage = (e) => {
            const d = JSON.parse(e.data);
            if(d.type === 'stream') appendBot(d.text);
            else if(d.type === 'image') addImg(d.url, d.text);
            else if(d.type === 'system') addMsg(d.text, 'sys-msg');
            else if(d.type === 'done') finalize();
        };
        let curDiv = null; let curRaw = "";
        function appendBot(t) {
            if(!curDiv) { curDiv = document.createElement(\"div\"); curDiv.className = \"msg r2-msg\"; document.getElementById(\"chat\").appendChild(curDiv); }
            curRaw += t; curDiv.innerHTML = marked.parse(curRaw);
            chatWrap.scrollTo(0, chatWrap.scrollHeight);
        }
        function addMsg(t, c) {
            const d = document.createElement(\"div\"); d.className = \"msg \" + c; d.innerText = t; 
            document.getElementById(\"chat\").appendChild(d); chatWrap.scrollTo(0, chatWrap.scrollHeight);
        }
        function addImg(u, t) {
            if(!u) return;
            const d = document.createElement(\"div\"); d.className = \"msg r2-msg\";
            d.innerHTML = `<b>${t}</b><br><img src=\"${u}\">`;
            document.getElementById(\"chat\").appendChild(d); chatWrap.scrollTo(0, chatWrap.scrollHeight);
        }
        function finalize() { curDiv = null; curRaw = \"\"; }
        function send() { const b = document.getElementById(\"msgBox\"); if(b.value) { ws.send(b.value); addMsg(b.value, 'user-msg'); b.value = \"\"; } }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_gui(): return HTML_TEMPLATE

# ==========================================
# 🧠 8. ROTEADOR LÓGICO (WEBSOCKET)
# ==========================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    async def processar_midia(caminho_bruto):
        if caminho_bruto and os.path.exists(caminho_bruto):
            nome = f"scan_{int(time.time())}_{os.path.basename(caminho_bruto)}"
            destino = os.path.join("static/media", nome)
            shutil.copy(caminho_bruto, destino)
            return f"/static/media/{nome}"
        return None

    try:
        while True:
            comando = await websocket.receive_text()
            cmd_l = comando.lower().strip()

            if cmd_l.startswith("/cmd "):
                sub = cmd_l.replace("/cmd ", "")
                # NOAA
                if sub == "solar" and noaa_ops:
                    path, _ = await asyncio.to_thread(noaa_ops.get_drap_map); url = await processar_midia(path)
                    await websocket.send_json({"type": "image", "url": url, "text": "📡 Mapa D-RAP"})
                elif sub == "radar":
                    m, p = await asyncio.to_thread(radar_ops.gerar_radar, "Ivinhema"); u = await processar_midia(p)
                    await websocket.send_json({"type": "image", "url": u, "text": m})
                elif sub == "iss":
                    p, m = await asyncio.to_thread(iss_ops.rastrear_iss); u = await processar_midia(p)
                    await websocket.send_json({"type": "image", "url": u, "text": m})
                continue

            if cmd_l.startswith("/img"):
                p = comando[4:].strip(); img = await asyncio.to_thread(img_ops.generate, p)
                n = f"gen_{int(time.time())}.png"; path = os.path.join("static/media", n); img.save(path)
                await websocket.send_json({"type": "image", "url": f"/static/media/{n}", "text": "✅ Renderização Concluída."})
                continue

            if cmd_l == "/doc sync":
                res = await asyncio.to_thread(rag_ops.sync); await websocket.send_json({"type": "system", "text": res})
                continue

            if ai_brain:
                prompt = f"<|im_start|>user\n{comando}<|im_end|>\n<|im_start|>assistant\n"
                stream = ai_brain(prompt, max_tokens=-1, stop=["<|im_end|>"], stream=True)
                for chunk in stream: await websocket.send_json({"type": "stream", "text": chunk["choices"][0]["text"]})
                await websocket.send_json({"type": "done"})

    except WebSocketDisconnect: pass

# ==========================================
# 🚀 9. LANÇAMENTO COM NGROK UPLINK
# ==========================================
if __name__ == "__main__":
    try:
        if NGROK_TOKEN and NGROK_TOKEN != "COLE_SEU_TOKEN_DO_NGROK_AQUI":
            ngrok.set_auth_token(NGROK_TOKEN)
            public_url = ngrok.connect(8000).public_url
            print(f"\n🌍 UPLINK REMOTO ATIVADO: {public_url}")
    except: pass
    uvicorn.run(app, host="0.0.0.0", port=8000)
