import os
import json
import datetime
import sys
import time
import asyncio
import urllib.request
import subprocess
import shutil
import re
import gc
from io import BytesIO

# ==========================================
# PROTOCOLO DE AUTO-AQUISIÇÃO LOGÍSTICA
# ==========================================

def extrair_artefato(url, pasta_destino, nome_arquivo, descricao):
    """Baixa arquivos pesados com barra de progresso tática."""
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
        
    caminho_completo = os.path.join(pasta_destino, nome_arquivo)
    
    if os.path.exists(caminho_completo):
        print(f"✅ [SISTEMA] {descricao} localizado. Status: OPERACIONAL.")
        return

    print(f"\n📥 [LOGÍSTICA] Artefato ausente. Iniciando extração de: {descricao}")
    print(f"⚠️ Alvo travado. Mantenha a conexão ativa...")

    def barra_progresso(blocos_lidos, tamanho_bloco, tamanho_total):
        if tamanho_total > 0:
            percentual = min(100, int((blocos_lidos * tamanho_bloco * 100) / tamanho_total))
            sys.stdout.write(f"\r⏳ Progresso da Extração: {percentual}% concluído...")
            sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, caminho_completo, reporthook=barra_progresso)
        print(f"\n✅ [SISTEMA] {descricao} instalado com sucesso em {pasta_destino}!")
    except Exception as e:
        print(f"\n❌ [ERRO CRÍTICO] Falha na extração de {nome_arquivo}: {e}")
        sys.exit(1)

def garantir_arsenal_completo():
    print("⚙️ [BOOTSTRAP] Verificando integridade do Arsenal Neural...")
    
    # 1. Cérebro de Visão (LLaVA 7B - Substitui o Llama puro para poder ver imagens)
    extrair_artefato(
        url="https://huggingface.co/mys/ggml_llava-v1.5-7b/resolve/main/ggml-model-q4_k.gguf",
        pasta_destino="models",
        nome_arquivo="ggml-model-q4_k.gguf",
        descricao="Cérebro de Visão Primário (Aprox. 4GB)"
    )

    # 2. Nervo Ótico (Projetor CLIP para conectar os "olhos" da IA)
    extrair_artefato(
        url="https://huggingface.co/mys/ggml_llava-v1.5-7b/resolve/main/mmproj-model-f16.gguf",
        pasta_destino="models",
        nome_arquivo="mmproj-model-f16.gguf",
        descricao="Nervo Ótico CLIP (Aprox. 600MB)"
    )

    # 3. Matriz de Fotorrealismo Extremo (Juggernaut XL v9 - Nível DSLR Profissional)
    caminho_juggernaut = os.path.join("visual_models", "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors")
    if os.path.exists(caminho_juggernaut):
        print(f"✅ [SISTEMA] Motor Juggernaut XL v9 (Aprox. 6.5GB) localizado. Status: OPERACIONAL.")
    else:
        print(f"\n📥 [LOGÍSTICA] Juggernaut XL v9 ausente. Iniciando extração via HuggingFace Hub...")
        print(f"⚠️ Download de ~6.5GB. Mantenha a conexão ativa...")
        try:
            from dotenv import load_dotenv
            from huggingface_hub import hf_hub_download
            load_dotenv()
            hf_token = os.getenv("HF_TOKEN")
            if not os.path.exists("visual_models"):
                os.makedirs("visual_models")
            hf_hub_download(
                repo_id="RunDiffusion/Juggernaut-XL-v9",
                filename="Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors",
                local_dir="visual_models",
                token=hf_token
            )
            print(f"✅ [SISTEMA] Juggernaut XL v9 instalado com sucesso!")
        except Exception as e:
            print(f"\n❌ [ERRO CRÍTICO] Falha na extração do Juggernaut XL v9: {e}")
            sys.exit(1)

# ==========================================
# MÓDULO DE MEMÓRIA CONTÍNUA (RAM & HD)
# ==========================================

# Memória RAM (Sessão atual - Limite de 20 mensagens para estabilidade da VRAM)
memoria_ram = []

def registrar_memoria_longo_prazo(usuario, resposta):
    """Grava cada interação no cofre para o FAISS ler no futuro."""
    pasta_docs = "static/docs"
    if not os.path.exists(pasta_docs):
        os.makedirs(pasta_docs)
        
    arquivo_memoria = os.path.join(pasta_docs, "Cofre_Memoria_R2.md")
    data_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Formata o registro como um documento tático
    registro = f"\n### [DATA: {data_hora}]\n**Comandante Teddy:** {usuario}\n**R2:** {resposta}\n---\n"
    
    # Escreve silenciosamente no disco
    with open(arquivo_memoria, "a", encoding="utf-8") as f:
        f.write(registro)

# ==========================================
# 🛠️ 1. MOTOR DE AUTO-INSTALAÇÃO (BOOTSTRAP)
# ==========================================
def garantir_ambiente():
    print("\n" + "="*50)
    print("⚙️ [BOOTSTRAP] SINCRONIZANDO ARSENAL TÁTICO")
    print("="*50)
    
    # Lista de dependências - Pillow é o nome do pacote para carregar 'PIL'
    deps = [
        "fastapi", "uvicorn", "websockets", "python-multipart", 
        "huggingface_hub", "requests", "psutil", "python-dotenv", 
        "greenlet", "playwright", "speedtest-cli",
        "feedparser", "geopy", "matplotlib", "beautifulsoup4",
        "diffusers", "transformers", "accelerate", "torch", "peft", 
        "PyPDF2", "sentence-transformers", "faiss-cpu", "numpy<2", 
        "pyngrok", "imageio-ffmpeg", "Pillow" 
    ]
    
    for package in deps:
        try:
            # Tratamento para nomes de importação diferentes dos nomes de instalação
            clean_name = package.split('<')[0] if '<' in package else package
            import_name = clean_name.replace("-", "_").replace("python-dotenv", "dotenv").replace("Pillow", "PIL")
            __import__(import_name)
        except ImportError:
            print(f"📦 Equipando R2 com: {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])

    # Tratamento especial para o Cérebro (llama-cpp)
    try:
        import llama_cpp
        print("🧠 [CÉREBRO]: Motor neural detectado e pronto.")
    except Exception as e:
        print(f"❌ Falha crítica: O motor neural não está instalado corretamente. Erro: {e}")
        print("Execute a instalação com CMAKE_ARGS=-DGGML_CUDA=on")


# DISPARA O INSTALADOR ANTES DE TUDO — DEPENDÊNCIAS PRIMEIRO
garantir_ambiente()
# SÓ ENTÃO verifica os modelos pesados (precisa de huggingface_hub, etc.)
garantir_arsenal_completo()

# ==========================================
# 📂 2. IMPORTAÇÕES TÁTICAS (AGORA É SEGURO)
# ==========================================
import numpy as np
from PIL import Image
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pyngrok import ngrok 
import torch
from diffusers import StableDiffusionXLPipeline, EulerAncestralDiscreteScheduler

# ==========================================
# 🔑 CONFIGURAÇÕES GERAIS
# ==========================================
NGROK_TOKEN = "COLE_SEU_TOKEN_AQUI"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
STOP_GEN = False

# ==========================================
# 📂 3. CARREGAMENTO DOS MÓDULOS DE FEATURES/
# ==========================================
def safe_import(module_name, class_name):
    try:
        import importlib
        mod = importlib.import_module(f"features.{module_name}")
        return getattr(mod, class_name)
    except Exception as e:
        print(f"⚠️ Módulo {class_name} ({module_name}) indisponível: {e}")
        return None

# Importando o arsenal completo
AirTrafficControl = safe_import("air_traffic", "AirTrafficControl")
AstroDefenseSystem = safe_import("astro_defense", "AstroDefenseSystem")
PizzaINTService = safe_import("pizzint_service", "PizzaINTService")
NOAAService = safe_import("noaa_service", "NOAAService")
GeoSeismicSystem = safe_import("geo_seismic", "GeoSeismicSystem")
SpeedTestModule = safe_import("net_speed", "SpeedTestModule")
VideoSurgeon = safe_import("video_ops", "VideoSurgeon")
# ── FALLBACK TÁTICO: se não achou em features/, tenta importar da raiz do projeto ──
if not VideoSurgeon:
    try:
        from video_ops import VideoSurgeon
        print("✂️ [TESOURA NEURAL]: Módulo carregado da raiz do projeto.")
    except Exception as e:
        print(f"⚠️ VideoSurgeon indisponível: {e}")
        VideoSurgeon = None
video_ops = VideoSurgeon() if VideoSurgeon else None

# ==========================================
# 📚 4. NÚCLEO RAG (PROCESSADOR DE PDFs)
# ==========================================
class KnowledgeBase:
    def __init__(self, docs_dir="static/docs"):
        self.docs_dir = docs_dir
        self.embedder = None
        self.index = None
        self.chunks = []
        self.arquivos_indexados = [] # 📋 Novo inventário tático
        os.makedirs(self.docs_dir, exist_ok=True)

    def sync(self):
        import faiss
        import PyPDF2
        from sentence_transformers import SentenceTransformer
        if not self.embedder: self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.chunks = []
        self.arquivos_indexados = [] # Reseta o inventário antes de ler
        
        arquivos = [f for f in os.listdir(self.docs_dir) if f.lower().endswith(('.pdf', '.md'))]
        if not arquivos: return "⚠️ Nenhum documento (.pdf ou .md) em static/docs."
        
        for arq in arquivos:
            try:
                full_path = os.path.join(self.docs_dir, arq)
                if arq.lower().endswith('.pdf'):
                    with open(full_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = "".join([p.extract_text() or "" for p in reader.pages])
                else:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                
                if text.strip():
                    self.arquivos_indexados.append(arq) # Registro de sucesso
                    for i in range(0, len(text), 800):
                        chunk = text[i:i+1000].strip()
                        if len(chunk) > 50: self.chunks.append(f"[Fonte: {arq}] {chunk}")
            except Exception: continue

        # ==========================================
        # BLINDAGEM NÍVEL MÁXIMO: PURIFICAÇÃO UTF-8
        # ==========================================
        import re
        
        textos_extraidos = []
        chunks_validos = [] # Guarda o pedaço original para não perder o sincronismo da página
        
        for pedaco in self.chunks:
            try:
                # 1. Extração
                if hasattr(pedaco, 'page_content'):
                    txt = pedaco.page_content
                elif isinstance(pedaco, dict) and 'text' in pedaco:
                    txt = pedaco['text']
                else:
                    txt = pedaco
                
                # 2. Conversão forçada
                txt_str = str(txt)
                
                # 3. O EXORCISMO: Força a codificação pura, destruindo caracteres ilegíveis para o Rust
                txt_str = txt_str.encode('utf-8', 'ignore').decode('utf-8')
                
                # 4. Remove caracteres fantasmas de controle da tabela ASCII e do Unicode
                txt_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', ' ', txt_str)
                txt_str = txt_str.strip()
                
                # 5. Só aprova se for texto útil
                if len(txt_str) > 10:
                    textos_extraidos.append(txt_str)
                    
                    # Atualiza o objeto original para o sistema RAG não se perder
                    if hasattr(pedaco, 'page_content'):
                        pedaco.page_content = txt_str
                        chunks_validos.append(pedaco)
                    elif isinstance(pedaco, dict) and 'text' in pedaco:
                        pedaco['text'] = txt_str
                        chunks_validos.append(pedaco)
                    else:
                        chunks_validos.append(txt_str)
            except Exception:
                pass

        if not textos_extraidos:
            return "❌ Erro Crítico: A extração falhou completamente."

        # Substitui a lista de rascunhos pela lista purificada e sincronizada
        self.chunks = chunks_validos

        print(f"⚙️ [RAG]: Motor iniciando leitura de {len(textos_extraidos)} blocos purificados...")
        
        # Vetorização (Agora o Rust não vai travar)
        embeddings = self.embedder.encode(textos_extraidos, convert_to_numpy=True, show_progress_bar=True)
        # ==========================================
        
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)
        return f"✅ Cérebro Atualizado! {len(self.arquivos_indexados)} arquivos integrados."

    def search(self, query):
        if not self.index: return None
        q_emb = self.embedder.encode([query], convert_to_numpy=True)
        _, indices = self.index.search(q_emb, 3)
        return "\n\n".join([self.chunks[idx] for idx in indices[0] if idx < len(self.chunks)])

# ==========================================
# 🎨 5. MOTOR VISUAL (REALISTIC VISION V5.1 - SD 1.5)
# ==========================================
class UltraVisualCore:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = None
        # Apontando para o motor que não explode a RAM
        self.caminho_modelo = "visual_models/Realistic_Vision_V5.1.safetensors"
        
    def load_engine(self):
        if self.pipe: return
        
        print(f"🎨 [VISUAL]: Acoplando Realistic Vision V5.1 à RTX 3050...")

        try:
            from diffusers import StableDiffusionPipeline # Usando o pipeline padrão (não o XL)
            import torch
            import gc

            # Esvazia a lixeira da RAM antes de iniciar
            gc.collect()
            if torch.cuda.is_available(): torch.cuda.empty_cache()

            # Carrega o modelo de 2GB de forma segura
            self.pipe = StableDiffusionPipeline.from_single_file(
                self.caminho_modelo,
                torch_dtype=torch.float16,
                use_safetensors=True,
                local_files_only=True
            )

            # ── BLINDAGEM DE VRAM PARA RTX 3050 ──────────────────────────────
            self.pipe.enable_model_cpu_offload()
            self.pipe.enable_attention_slicing()
            # ─────────────────────────────────────────────────────────────────

            print("🎨 [VISUAL]: Fotorrealismo Operacional. Pronto para combate.")
        except Exception as e:
            print(f"❌ [ERRO VISUAL]: Falha ao acoplar a matriz. Detalhes: {e}")
            self.pipe = None

    def generate(self, prompt):
        if not self.pipe: self.load_engine()
        if not self.pipe:
            raise RuntimeError("Motor visual não inicializado.")

        import gc
        import torch
        gc.collect()
        if torch.cuda.is_available(): torch.cuda.empty_cache()

        # Prompt engineering para SD 1.5 (Fotorrealismo)
        pos = (
            f"RAW photo, {prompt}, 8k uhd, dslr, soft lighting, high quality, film grain, Fujifilm XT4"
        )
        neg = (
            "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime:1.4), "
            "text, close up, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, "
            "morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, "
            "blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions"
        )

        # SD 1.5 opera perfeitamente em modo retrato (512x768) na RTX 3050
        with torch.inference_mode():
            image = self.pipe(
                prompt=pos,
                negative_prompt=neg,
                num_inference_steps=25,
                height=768,
                width=512,
                guidance_scale=7.5
            ).images[0]
        return image

# ==========================================
# 🧠 6. INICIALIZAÇÃO DE SISTEMAS
# ==========================================
os.makedirs("static/media", exist_ok=True)
rag_ops = KnowledgeBase()
img_ops = UltraVisualCore()
radar_ops = AirTrafficControl() if AirTrafficControl else None
astro_ops = AstroDefenseSystem() if AstroDefenseSystem else None
pizza_ops = PizzaINTService(config={}) if PizzaINTService else None
noaa_ops = NOAAService() if NOAAService else None
sismo_ops = GeoSeismicSystem() if GeoSeismicSystem else None
speed_ops = SpeedTestModule() if SpeedTestModule else None

try:
    from llama_cpp import Llama
    print("🧠 [CÉREBRO DE TEXTO] Iniciando motor Neural otimizado para RTX 3050...")
    
    # Reduzi o contexto para 8192 (ainda é enorme, o equivalente a um livro pequeno) 
    # e ajustei as camadas para 20. Assim a sua placa não "explode" de falta de VRAM!
    ai_brain = Llama(
            model_path="models/Dolphin3.0-Llama3.1-8B-Q4_K_M.gguf", 
            n_ctx=4096, 
            n_gpu_layers=20, 
            verbose=False
        )
except Exception as e:
    print(f"❌ Erro ao iniciar IA de Texto: {e}")
    ai_brain = None

# ==========================================
# 🌐 7. SERVIDOR E INTERFACE CUSTOMIZADA
# ==========================================
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/stop")
async def stop_gen_route():
    global STOP_GEN
    STOP_GEN = True
    return {"status": "ok"}

# O SEU HTML_TEMPLATE INTEGRADO
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
    <title>R2 Tactical OS</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
    <style>
        :root { --bg: #050510; --panel: rgba(10, 10, 26, 0.95); --neon: #00ffff; --neon-green: #00ff00; --user-bg: rgba(0, 51, 51, 0.7); --bot-bg: rgba(0, 26, 0, 0.7); }

        /* ESTÚDIO DE VÍDEO (MODAL) */
        #video-studio { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: var(--panel); border: 2px solid var(--neon); padding: 20px; border-radius: 12px; z-index: 2000; width: 90%; max-width: 800px; box-shadow: 0 0 30px rgba(0, 255, 255, 0.2); }
        .studio-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #004444; padding-bottom: 10px; margin-bottom: 15px; }
        .studio-header h3 { color: var(--neon); font-family: monospace; }
        .close-btn { background: red; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: bold; }
        
        /* O Frame de Pré-visualização */
        .preview-box { width: 100%; aspect-ratio: 9/16; background: #000 url('https://images.unsplash.com/photo-1611162617474-5b21e879e113?q=80&w=400&auto=format&fit=crop') center/cover; position: relative; border-radius: 8px; overflow: hidden; max-height: 400px; margin: 0 auto; border: 1px solid #333; }
        
        /* A Legenda Fake (Drag and Drop simulado via CSS para posição) */
        #preview-subtitle { position: absolute; bottom: 20%; left: 50%; transform: translateX(-50%); text-align: center; font-family: 'Arial', sans-serif; font-size: 24px; font-weight: bold; color: #ffffff; text-transform: uppercase; text-shadow: 2px 2px 0px #000, -2px -2px 0px #000, 2px -2px 0px #000, -2px 2px 0px #000; white-space: nowrap; transition: all 0.2s; cursor: pointer; }
        
        /* Controles de Edição */
        .controls-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px; background: rgba(0,0,0,0.5); padding: 15px; border-radius: 8px; }
        .control-group { display: flex; flex-direction: column; gap: 5px; }
        .control-group label { color: #aaa; font-size: 0.85rem; font-weight: bold; }
        .control-input { background: #111; color: #fff; border: 1px solid #004444; padding: 8px; border-radius: 4px; }
        .action-btn { grid-column: span 2; background: var(--neon); color: #000; font-weight: bold; padding: 12px; border: none; border-radius: 6px; cursor: pointer; text-transform: uppercase; margin-top: 10px; transition: 0.3s; }
        .action-btn:hover { background: #fff; box-shadow: 0 0 15px var(--neon); }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background-color: var(--bg); color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; flex-direction: column; height: 100vh; overflow: hidden; background-image: radial-gradient(circle at 50% 0%, #0a192f 0%, var(--bg) 70%); }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: #004444; border-radius: 3px; }
        
        /* Cabeçalho */
        #header { background: var(--panel); padding: 15px 20px; border-bottom: 1px solid rgba(0, 255, 255, 0.2); display: flex; justify-content: space-between; align-items: center; z-index: 10; box-shadow: 0 4px 15px rgba(0,255,255,0.05); }
        .header-left { display: flex; align-items: center; gap: 12px; }
        #menu-btn { background: none; border: none; color: var(--neon); font-size: 26px; cursor: pointer; transition: transform 0.2s; }
        #menu-btn:hover { transform: scale(1.1); text-shadow: 0 0 8px var(--neon); }
        h2 { font-size: 1.2rem; color: var(--neon); font-family: 'Courier New', monospace; letter-spacing: 1px; }
        .status { font-size: 0.9rem; color: var(--neon-green); text-shadow: 0 0 5px var(--neon-green); white-space: nowrap; }
        
        /* Menu Lateral responsivo */
        #side-menu { position: fixed; left: -320px; top: 0; width: 300px; max-width: 80vw; height: 100%; background: var(--panel); border-right: 1px solid rgba(0,255,255,0.3); transition: 0.4s cubic-bezier(0.4, 0, 0.2, 1); z-index: 1000; padding: 20px; display: flex; flex-direction: column; gap: 12px; box-shadow: 5px 0 20px rgba(0,0,0,0.8); overflow-y: auto; }
        #side-menu.open { left: 0; }
        .mod-btn { background: rgba(0, 51, 51, 0.6); border: 1px solid #004444; color: #fff; padding: 12px; border-radius: 6px; cursor: pointer; text-align: left; transition: all 0.3s; font-weight: bold; font-size: 0.95rem; }
        .mod-btn:hover { background: var(--neon); color: #000; box-shadow: 0 0 10px var(--neon); transform: translateX(5px); }
        
        /* Área de Chat */
        #chat-wrapper { flex: 1; overflow-y: auto; display: flex; flex-direction: column; align-items: center; scroll-behavior: smooth; padding-bottom: 20px; }
        #chat { width: 100%; max-width: 1000px; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        
        /* Mensagens */
        @keyframes slideIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
        .msg { max-width: 85%; padding: 12px 16px; border-radius: 10px; line-height: 1.5; font-size: 0.95rem; animation: slideIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; box-shadow: 0 4px 10px rgba(0,0,0,0.4); word-wrap: break-word; }
        .user-msg { align-self: flex-end; background: var(--user-bg); border: 1px solid var(--neon); border-bottom-right-radius: 2px; }
        .r2-msg { align-self: flex-start; background: var(--bot-bg); border: 1px solid var(--neon-green); width: 100%; border-top-left-radius: 2px; }
        .sys-msg { color: #ffbb00; text-align: center; font-family: monospace; border: 1px dashed #ffbb00; background: rgba(255, 187, 0, 0.1); width: 100%; align-self: center; }
        
        /* Indicador de Processamento */
        .typing-indicator { display: flex; align-items: center; gap: 5px; padding: 12px 16px; width: fit-content; }
        .typing-indicator span { display: block; width: 6px; height: 6px; background-color: var(--neon-green); border-radius: 50%; box-shadow: 0 0 5px var(--neon-green); animation: bounce 1.4s infinite ease-in-out both; }
        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); opacity: 0.3; } 40% { transform: scale(1); opacity: 1; } }

        /* Área de Input Blindada */
        #input-wrapper { background: var(--panel); padding: 12px; border-top: 1px solid rgba(0, 255, 255, 0.2); box-shadow: 0 -4px 15px rgba(0,0,0,0.6); flex-shrink: 0; }
        #input-area { display: flex; gap: 10px; max-width: 1000px; margin: 0 auto; width: 100%; align-items: flex-end; }
        textarea { flex: 1; background: rgba(0,0,0,0.8); color: #fff; border: 1px solid #004444; border-radius: 8px; padding: 12px; resize: none; font-family: inherit; font-size: 1rem; max-height: 120px; transition: border 0.3s; width: 100%; }
        textarea:focus { outline: none; border-color: var(--neon); box-shadow: inset 0 0 8px rgba(0,255,255,0.2); }
        .send-btn { background: #006666; color: #fff; border: none; padding: 12px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; transition: all 0.3s; text-transform: uppercase; font-size: 0.9rem; height: 45px; }
        .send-btn:hover { background: var(--neon); color: #000; box-shadow: 0 0 15px var(--neon); transform: translateY(-2px); }
        
        #overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); backdrop-filter: blur(3px); z-index: 999; }
        #overlay.active { display: block; }

        /* RESPONSIVIDADE TÁTICA MOBILE */
        @media (max-width: 768px) {
            #header { padding: 10px 15px; }
            h2 { font-size: 1.1rem; }
            .status { font-size: 0.8rem; }
            #chat { padding: 15px 10px; gap: 12px; }
            .msg { max-width: 95%; padding: 10px 12px; font-size: 0.9rem; }
            #input-wrapper { padding: 10px; padding-bottom: max(10px, env(safe-area-inset-bottom)); }
            #input-area { gap: 8px; }
            textarea { padding: 10px; font-size: 0.95rem; }
            .send-btn { padding: 0 15px; font-size: 0.8rem; }
        }
    </style>
</head>
<body>
    <div id="header">
        <div class="header-left"><button id="menu-btn" onclick="toggleMenu()">☰</button><h2>⚡ R2 OS</h2></div>
        <div class="status" id="conn-status">● ONLINE</div>
    </div>
    <div id="overlay" onclick="toggleMenu()"></div>
    <div id="video-studio">
        <div class="studio-header">
            <h3>🎬 Operação: Tesoura Neural</h3>
            <button class="close-btn" onclick="document.getElementById('video-studio').style.display='none'">X</button>
        </div>
        
        <div class="preview-box">
            <div id="preview-subtitle">A JORNADA DO HERÓI<br>COMEÇA AQUI!</div>
        </div>
        
        <div class="controls-grid">
            <div class="control-group">
                <label>URL do YouTube:</label>
                <input type="text" id="vid-url" class="control-input" placeholder="https://youtube.com/...">
            </div>
            <div class="control-group">
                <label>Status da Legenda:</label>
                <div style="display:flex; gap:10px; align-items:center;">
                    <input type="checkbox" id="sub-active" checked style="width:20px; height:20px;">
                    <span>Ativar Legendas</span>
                </div>
            </div>
            <div class="control-group">
                <label>IA decide posição?</label>
                <div style="display:flex; gap:10px; align-items:center;">
                    <input type="checkbox" id="sub-pos-auto" checked onchange="document.getElementById('sub-pos').disabled = this.checked">
                    <span>Automático</span>
                </div>
            </div>
            <div class="control-group">
                <label>Qtd. de Cortes Virais:</label>
                <input type="number" id="vid-cuts" class="control-input" value="3" min="1" max="10">
            </div>
            
            <div class="control-group">
                <label>Cor da Legenda:</label>
                <input type="color" id="sub-color" class="control-input" value="#ffffff" oninput="updatePreview()">
            </div>
            <div class="control-group">
                <label>Tamanho (Fonte):</label>
                <input type="range" id="sub-size" min="14" max="40" value="24" oninput="updatePreview()">
            </div>
            <div class="control-group">
                <label>Posição Vertical (Y):</label>
                <input type="range" id="sub-pos" min="5" max="95" value="20" oninput="updatePreview()">
            </div>
            <div class="control-group">
                <label>Estilo (Borda/Fundo):</label>
                <select id="sub-style" class="control-input" onchange="updatePreview()">
                    <option value="outline">Borda Preta Grossa</option>
                    <option value="shadow">Sombra Suave</option>
                    <option value="box">Fundo Preto Transparente</option>
                    <option value="yellow">Destaque Amarelo (Estilo Hormozi)</option>
                </select>
            </div>
            
            <button class="action-btn" onclick="startVideoExtraction()">🚀 Iniciar Extração Tática</button>
        </div>
    </div>
    <div id="side-menu">
        <button class="mod-btn" onclick="execCmd('/doc sync', '📚 Sincronizando Matriz...')">📚 Sincronizar PDFs</button>
        <button class="mod-btn" onclick="execCmd('/doc list', '📋 Verificando Inventário...')">📋 Listar Arquivos</button>
        <button class="mod-btn" onclick="execCmd('/cmd radar', '📡 Escaneando Radar...')">📡 Radar de Voos</button>
        <button class="mod-btn" onclick="execCmd('/cmd astro', '☄️ Consultando NASA...')">☄️ Defesa Planetária</button>
        <button class="mod-btn" onclick="execCmd('/cmd pizza', '🍕 Checando PizzINT...')">🍕 Monitor PizzINT</button>
        <button class="mod-btn" onclick="execCmd('/cmd solar', '☀️ Atividade Solar...')">☀️ Clima Espacial</button>
        <button class="mod-btn" onclick="document.getElementById('video-studio').style.display='block'">🎬 Estúdio de Cortes</button>
    </div>
    <div id="chat-wrapper"><div id="chat"></div></div>
    <div id="input-wrapper">
        <div id="input-area">
            <textarea id="msgBox" placeholder="Aguardando ordens..." rows="1" oninput="this.style.height = ''; this.style.height = Math.min(this.scrollHeight, 120) + 'px'" onkeypress="if(event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMsg(); }"></textarea>
            <button class="send-btn" onclick="sendMsg()">Enviar</button>
        </div>
    </div>
    
    <script>
        const currentUrl = window.location.href;
        let ws;

        function conectarMatriz() {
            // Suporte tático para conexões seguras (https) ou locais (http)
            const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
            ws = new WebSocket(`${protocol}${window.location.host}/ws`);

            ws.onmessage = function(event) {
                let data = JSON.parse(event.data);
                if(data.type === "system") {
                    appendMessage("Sistema", data.text);
                    hideTyping();
                } else if (data.type === "stream") {
                    let chatBox = document.getElementById("chat");
                    let lastMsg = chatBox.lastElementChild;
                    if(lastMsg && lastMsg.classList.contains("r2-msg")) {
                        let contentDiv = lastMsg.querySelector(".bot-content");
                        contentDiv.innerHTML += data.text;
                    } else {
                        appendMessage("R2", data.text);
                    }
                    chatBox.scrollTop = chatBox.scrollHeight;
                } else if (data.type === "done") {
                    let chatBox = document.getElementById("chat");
                    let lastMsg = chatBox.lastElementChild;
                    if(lastMsg && lastMsg.classList.contains("r2-msg")) {
                        let contentDiv = lastMsg.querySelector(".bot-content");
                        try {
                            contentDiv.innerHTML = marked.parse(contentDiv.innerHTML);
                            contentDiv.querySelectorAll('pre code').forEach((block) => {
                                hljs.highlightElement(block);
                            });
                        } catch(e) { console.error("Erro no parser", e); }
                    }
                    hideTyping();
                } else if (data.type === "image") {
                    hideTyping();
                    appendMessage("Sistema", `<b>${data.text}</b><br><img src="${data.url}" style="max-width:100%; border-radius: 8px; margin-top: 10px; box-shadow: 0 4px 8px rgba(0,255,255,0.2);">`);
                }
            };

            ws.onclose = function() {
                appendMessage("Sistema", "❌ Conexão neural cortada. Tentando auto-reparação em 3 segundos...");
                hideTyping();
                setTimeout(conectarMatriz, 3000);
            };
            
            ws.onerror = function(err) {
                console.error("Erro no Radar WebSocket: ", err);
            };
        }

        function appendMessage(sender, text) {
            let chatBox = document.getElementById("chat");
            let msgDiv = document.createElement("div");
            msgDiv.className = "msg " + (sender === "Teddy" ? "user-msg" : "r2-msg");
            msgDiv.innerHTML = `<strong>${sender}:</strong> <div class="bot-content">${text}</div>`;
            chatBox.appendChild(msgDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function showTyping() {
            let indicator = document.getElementById("typing-indicator");
            if (!indicator) {
                indicator = document.createElement("div");
                indicator.id = "typing-indicator";
                indicator.className = "msg r2-msg typing-indicator";
                indicator.innerHTML = "<span></span><span></span><span></span>";
                document.getElementById("chat").appendChild(indicator);
            }
            indicator.style.display = "flex";
        }

        function hideTyping() {
            let indicator = document.getElementById("typing-indicator");
            if (indicator) indicator.style.display = "none";
        }

        // --- BOTÕES E COMANDOS ---

        function sendMsg() {
            let input = document.getElementById("msgBox");
            let msg = input.value.trim();
            if(msg) {
                if(!ws || ws.readyState !== WebSocket.OPEN) {
                    alert("⚠️ Radar offline! Aguarde a reconexão com o servidor...");
                    return;
                }
                appendMessage("Teddy", msg);
                ws.send(msg);
                input.value = "";
                input.style.height = '';
                showTyping();
            }
        }

        function execCmd(cmd, fakeMsg) {
            if(!ws || ws.readyState !== WebSocket.OPEN) {
                alert("⚠️ Radar offline! Servidor desconectado.");
                return;
            }
            toggleMenu();
            appendMessage("Teddy", fakeMsg);
            ws.send(cmd);
            showTyping();
        }

        function toggleMenu() { 
            document.getElementById('side-menu').classList.toggle('open'); 
            document.getElementById('overlay').classList.toggle('active'); 
        }

        // --- MÓDULO DE VÍDEO (TESOURA NEURAL) ---

        function updatePreview() {
            const sub = document.getElementById('preview-subtitle');
            const color = document.getElementById('sub-color').value;
            const size = document.getElementById('sub-size').value;
            const pos = document.getElementById('sub-pos').value;
            const style = document.getElementById('sub-style').value;
            
            sub.style.color = color;
            sub.style.fontSize = size + 'px';
            sub.style.bottom = pos + '%';
            
            if(style === 'outline') {
                sub.style.textShadow = '2px 2px 0px #000, -2px -2px 0px #000, 2px -2px 0px #000, -2px 2px 0px #000';
                sub.style.backgroundColor = 'transparent';
                sub.style.padding = '0';
            } else if (style === 'shadow') {
                sub.style.textShadow = '4px 4px 8px rgba(0,0,0,0.8)';
                sub.style.backgroundColor = 'transparent';
                sub.style.padding = '0';
            } else if (style === 'box') {
                sub.style.textShadow = 'none';
                sub.style.backgroundColor = 'rgba(0,0,0,0.7)';
                sub.style.padding = '5px 15px';
                sub.style.borderRadius = '8px';
            } else if (style === 'yellow') {
                sub.style.color = '#ffff00';
                sub.style.textShadow = '3px 3px 0px #000';
                sub.style.backgroundColor = 'transparent';
                sub.style.padding = '0';
            }
        }
        
        function startVideoExtraction() {
            const url = document.getElementById('vid-url').value;
            if(!url) { alert("Comandante, insira o link do alvo!"); return; }
            
            const config = {
                url: url,
                active: document.getElementById('sub-active').checked,
                autoPos: document.getElementById('sub-pos-auto').checked,
                color: document.getElementById('sub-color').value,
                size: document.getElementById('sub-size').value,
                style: document.getElementById('sub-style').value,
                pos: document.getElementById('sub-pos').value
            };
            
            document.getElementById('video-studio').style.display = 'none';
            execCmd(`/vid extract ${JSON.stringify(config)}`, '🎬 Operação iniciada. IA calculando tempos e enquadramento...');
        }

        // LIGAR OS MOTORES
        conectarMatriz();
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
    
    async def processar_midia(caminho):
        if caminho and os.path.exists(caminho):
            nome = f"scan_{int(time.time())}_{os.path.basename(caminho)}"
            shutil.copy(caminho, os.path.join("static/media", nome))
            return f"/static/media/{nome}"
        return None

    sys_prompt = "Você é o R2, um assistente tático de IA. Seja preciso, estratégico e direto."

    try:
        while True:
            comando = await websocket.receive_text()
            cmd_l = comando.lower().strip()

            # Módulos Táticos
            if cmd_l.startswith("/cmd "):
                sub = cmd_l.replace("/cmd ", "")
                if sub == "radar" and radar_ops:
                    p, q, m = await asyncio.to_thread(radar_ops.radar_scan, "Ivinhema")
                    u = await processar_midia(p); await websocket.send_json({"type": "image", "url": u, "text": m})
                elif sub == "astro" and astro_ops:
                    r, i, n = await asyncio.to_thread(astro_ops.get_asteroid_report)
                    await websocket.send_json({"type": "stream", "text": r}); await websocket.send_json({"type": "done"})
                elif sub == "pizza" and pizza_ops:
                    st = pizza_ops.get_status()
                    await websocket.send_json({"type": "system", "text": f"🍕 PizzINT: {st['level']:.0f} pedidos/h."})
                elif sub == "solar" and noaa_ops:
                    p, _ = await asyncio.to_thread(noaa_ops.get_drap_map); u = await processar_midia(p)
                    await websocket.send_json({"type": "image", "url": u, "text": "☀️ Mapa D-RAP"})
                continue

            # Operação Tesoura Neural
            if cmd_l.startswith("/vid extract"):
                if not video_ops:
                    await websocket.send_json({"type": "system", "text": "❌ Módulo de vídeo inoperante. Verifique se video_ops.py está na raiz do projeto."})
                    continue
                
                json_str = comando.replace("/vid extract ", "").strip()
                config = json.loads(json_str)
                
                await websocket.send_json({"type": "system", "text": "🎬 Tesoura Neural ativada. Operação pesada iniciada — fique na escuta, Comandante..."})
                
                # ── CALLBACK DE PROGRESSO ──
                # Permite que a thread do vídeo envie status em tempo real pro chat
                loop = asyncio.get_event_loop()
                def progresso_callback(msg):
                    asyncio.run_coroutine_threadsafe(
                        websocket.send_json({"type": "system", "text": msg}),
                        loop
                    )
                
                caminho_clip = await asyncio.to_thread(video_ops.processar_alvo, config, ai_brain, progresso_callback)
                
                if caminho_clip:
                    await websocket.send_json({
                        "type": "system", 
                        "text": f"✅ Corte finalizado!<br><video width='100%' controls style='border-radius:8px;margin-top:10px;'><source src='{caminho_clip}' type='video/mp4'></video>"
                    })
                else:
                    await websocket.send_json({"type": "system", "text": "❌ Falha crítica ao renderizar. Verifique o terminal para detalhes."})
                continue

            # Geração de Imagem
            if cmd_l.startswith("/img "):
                p = comando[5:]; img = await asyncio.to_thread(img_ops.generate, p)
                n = f"gen_{int(time.time())}.png"; path = os.path.join("static/media", n); img.save(path)
                await websocket.send_json({"type": "image", "url": f"/static/media/{n}", "text": "✅ Renderizada."})
                continue

            # Sincronização Manual dos PDFs
            if cmd_l == "/doc sync":
                res = await asyncio.to_thread(rag_ops.sync); await websocket.send_json({"type": "system", "text": res})
                continue

            # Listagem de Arquivos Indexados
            if cmd_l == "/doc list":
                if hasattr(rag_ops, 'arquivos_indexados') and rag_ops.arquivos_indexados:
                    lista = ", ".join(rag_ops.arquivos_indexados)
                    res = f"📋 **Arquivos no Córtex:** {lista}"
                else:
                    res = "⚠️ Nenhum arquivo indexado no momento."
                await websocket.send_json({"type": "system", "text": res}); continue

            # ==========================================
            # 🧠 ONISCIÊNCIA: TEXTO + RAG AUTOMÁTICO
            # ==========================================
            if ai_brain:
                # 1. Guarda na RAM
                memoria_ram.append(f"Teddy: {comando}")
                if len(memoria_ram) > 20: 
                    memoria_ram.pop(0)

                # 1. Pesquisa invisível no Banco de Dados
                contexto_recuperado = await asyncio.to_thread(rag_ops.search, comando)
                
                # 2. Constrói a linha de raciocínio
                prompt = f"<|im_start|>system\n{sys_prompt}\n"
                
                # 3. Injeta a sabedoria dos livros apenas se achar algo relevante
                if contexto_recuperado:
                    prompt += f"\n[DADOS DOS MANUAIS TÁTICOS (PDFs)]:\n{contexto_recuperado}\nUse essas informações para basear sua resposta.\n"
                
                prompt += "<|im_end|>\n"
                
                # 4. Adiciona o histórico recente (memória da conversa)
                # Converte a RAM para o formato ChatML esperado pelo Dolphin
                for m in memoria_ram[:-1]:
                    if m.startswith("Teddy: "):
                        prompt += f"<|im_start|>user\n{m[7:]}<|im_end|>\n"
                    elif m.startswith("R2: "):
                        prompt += f"<|im_start|>assistant\n{m[4:]}<|im_end|>\n"
                
                # 5. Adiciona o comando atual
                prompt += f"<|im_start|>user\n{comando}<|im_end|>\n<|im_start|>assistant\n"

                # 6. Gera a resposta e envia
                global STOP_GEN
                STOP_GEN = False
                stream = ai_brain(prompt, max_tokens=-1, stop=["<|im_end|>"], stream=True, temperature=0.5)
                
                resp_completa = ""
                for chunk in stream:
                    if STOP_GEN:
                        STOP_GEN = False
                        break
                    token = chunk["choices"][0]["text"]
                    resp_completa += token
                    await websocket.send_json({"type": "stream", "text": token})
                
                await websocket.send_json({"type": "done"})
                
                # 3. Guarda a resposta da IA na RAM
                memoria_ram.append(f"R2: {resp_completa}")
                # 4. Grava no Cofre de Longo Prazo (HD)
                registrar_memoria_longo_prazo(comando, resp_completa)

    except WebSocketDisconnect: pass

if __name__ == "__main__":
    try:
        if NGROK_TOKEN and NGROK_TOKEN != "COLE_SEU_TOKEN_AQUI":
            ngrok.set_auth_token(NGROK_TOKEN)
            print(f"\n🌍 UPLINK REMOTO: {ngrok.connect(8000).public_url}")
    except: pass
    uvicorn.run(app, host="0.0.0.0", port=8000)