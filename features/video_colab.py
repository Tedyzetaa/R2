import os
import time
import json
import re
import cv2
import yt_dlp
import whisper
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from moviepy.config import change_settings

# ⚠️ CAMINHO DO IMAGEMAGICK PARA NUVEM (LINUX / COLAB)
change_settings({"IMAGEMAGICK_BINARY": "convert"})

class VideoSurgeon:
    def __init__(self):
        print("✂️ [TESOURA NEURAL - MODO NUVEM]: Inicializando Córtex de Edição Dinâmica...")
        self.whisper_model = whisper.load_model("base")
        self.temp_dir = "temp_video"
        self.out_dir = "static/media"
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.out_dir, exist_ok=True)

    def detectar_rosto_x(self, video_path, tempo_inicio, tempo_fim):
        """Olho de Águia V2: Faz uma varredura em 5 momentos diferentes do corte. 
           Trava a mira no maior rosto (alvo principal)."""
        try:
            cap = cv2.VideoCapture(video_path)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            duracao = tempo_fim - tempo_inicio
            passo = duracao / 5 
            
            for i in range(1, 5):
                tempo_teste = tempo_inicio + (passo * i)
                cap.set(cv2.CAP_PROP_POS_MSEC, tempo_teste * 1000)
                ret, frame = cap.read()
                
                if ret:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    
                    if len(faces) > 0:
                        cap.release()
                        maior_area = 0
                        melhor_x = None
                        for (x, y, w, h) in faces:
                            area = w * h
                            if area > maior_area:
                                maior_area = area
                                melhor_x = x + (w / 2)
                        return melhor_x 
            cap.release()
        except Exception as e:
            print(f"⚠️ Alerta no radar visual: {e}")
        return None 

    def analisar_com_llama(self, transcricao_str, ai_brain, rag_context=None):
        print("🧠 [CÉREBRO]: Analisando roteiro com a Sabedoria Tática dos Manuais (RAG)...")
        
        regras_rag = f"\n[SABEDORIA TÁTICA (RAG)]:\n{rag_context}\n" if rag_context else ""
        
        prompt = f"""<|im_start|>system
Você é um Diretor de TV especialista em retenção viral. Analise a transcrição e extraia os melhores momentos.{regras_rag}
Regra 1: Você OBRIGATORIAMENTE deve escolher de 2 a 4 trechos separados para criar um clipe dinâmico.
Regra 2: A soma total deve estar entre 60 e 180 segundos.
Regra 3: Defina 'position' (0-100) para a legenda (20=base, 50=centro, 80=topo).
Responda APENAS com JSON. Exemplo: {{"cortes": [{{"start": 10, "end": 40}}, {{"start": 80, "end": 110}}], "position": 20}}<|im_end|>
<|im_start|>user
{transcricao_str}<|im_end|>
<|im_start|>assistant
"""
        stream = ai_brain(prompt, max_tokens=400, stop=["<|im_end|>"], temperature=0.3)
        resposta = stream["choices"][0]["text"].strip()
        
        match = re.search(r'\{.*?\}', resposta, re.DOTALL)
        if match:
            try:
                dados = json.loads(match.group(0))
                return dados.get("cortes", [{"start": 10, "end": 70}]), dados.get("position", 20)
            except: pass
        return [{"start": 10, "end": 70}], 20

    def processar_alvo(self, config, ai_brain=None, callback=None, rag_context=None):
        def log(msg):
            print(msg)
            if callback:
                try: callback(msg)
                except Exception: pass

        url = config.get("url")
        cor = config.get("color", "#ffffff")
        tamanho = int(config.get("size", 24)) * 2 
        estilo = config.get("style", "outline")
        sub_enabled = config.get("active", True)
        auto_pos = config.get("autoPos", True)
        
        log(f"📥 <b>[Fase 1/5] Infiltração:</b> Baixando alvo...")
        ydl_opts = {'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 'outtmpl': f'{self.temp_dir}/alvo_%(id)s.%(ext)s', 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)

        log("🎧 <b>[Fase 2/5] Interrogatório:</b> Transcrevendo áudio...")
        resultado = self.whisper_model.transcribe(video_path, fp16=False)

        transcricao_str = "".join([f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}\n" for s in resultado["segments"]])
        if len(transcricao_str) > 7500:
            log("⚠️ <b>[BLINDAGEM]:</b> Fatiando texto para VRAM...")
            transcricao_str = transcricao_str[:7500]

        log("🧠 <b>[Fase 3/5] Decisão:</b> LLaMA costurando o roteiro via RAG...")
        cortes, pos_sugerida = self.analisar_com_llama(transcricao_str, ai_brain, rag_context)
        y_final = pos_sugerida if auto_pos else config.get("pos", 20)

        log("🎯 <b>[Fase 4/5] Auto-Framing e Legendas em Lote...</b>")
        video_original = VideoFileClip(video_path)
        clipes_finais = []
        
        cor_fundo = "black" if estilo == "box" else "transparent"
        cor_texto = "yellow" if estilo == "yellow" else cor

        for idx, corte in enumerate(cortes):
            st, nd = corte["start"], corte["end"]
            if st >= video_original.duration: continue
            
            log(f"✂️ Processando pedaço {idx+1}/{len(cortes)}...")
            sub = video_original.subclip(st, min(nd, video_original.duration))
            
            # Enquadramento Dinâmico (Olho de Águia V2)
            cx = self.detectar_rosto_x(video_path, st, nd)
            w, h = sub.size
            tw = int(h * 9/16)
            x_center = cx if cx else (w / 2)
            x_center = max(tw/2, min(w - tw/2, x_center))
            sub = sub.crop(x1=x_center - tw/2, y1=0, x2=x_center + tw/2, y2=h)
            
            y_pixels = sub.h - (sub.h * (int(y_final) / 100))
            legendas = []
            if sub_enabled:
                for seg in resultado["segments"]:
                    if seg["end"] > st and seg["start"] < nd:
                        txt = TextClip(seg["text"].strip().upper(), fontsize=tamanho, color=cor_texto, bg_color=cor_fundo, font="Arial", method='caption', size=(int(sub.w * 0.85), None))
                        txt = txt.set_position(('center', y_pixels)).set_start(max(0, seg["start"]-st)).set_end(min(sub.duration, seg["end"]-st)).crossfadein(0.15).crossfadeout(0.15)
                        legendas.append(txt)
            
            clipes_finais.append(CompositeVideoClip([sub] + legendas) if legendas else sub)

        log(f"🔥 <b>[Fase 5/5] Fusão Final...</b>")
        nome_saida = f"corte_viral_costurado_{int(time.time())}.mp4"
        caminho_final = os.path.join(self.out_dir, nome_saida)
        
        try:
            final = concatenate_videoclips(clipes_finais, method="compose")
            final.write_videofile(caminho_final, codec="libx264", audio_codec="aac", fps=30, preset="ultrafast")
            return f"/static/media/{nome_saida}"
        except Exception as e:
            log(f"❌ <b>ERRO:</b> {e}")
            return None
        finally:
            video_original.close()
            for c in clipes_finais: c.close()
            if os.path.exists(video_path): os.remove(video_path)