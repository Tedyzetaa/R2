import os
import time
import json
import re
import cv2
import yt_dlp
import whisper
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from moviepy.config import change_settings

# ⚠️ SEU CAMINHO DO IMAGEMAGICK
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})

class VideoSurgeon:
    def __init__(self):
        print("✂️ [TESOURA NEURAL V2]: Inicializando Córtex de Costura Dinâmica...")
        self.whisper_model = whisper.load_model("base")
        self.temp_dir = "temp_video"
        self.out_dir = "static/media"
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.out_dir, exist_ok=True)

    def detectar_rosto_x(self, video_path, tempo_inicio, tempo_fim):
        """Olho de Águia V2: Faz uma varredura em 4 momentos diferentes do corte. 
           Se achar múltiplos rostos, trava a mira no maior (alvo principal)."""
        try:
            cap = cv2.VideoCapture(video_path)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            duracao = tempo_fim - tempo_inicio
            passo = duracao / 5 # Fatiamos o tempo em 5 partes para escanear
            
            # Testa 4 frames diferentes dentro do corte para garantir que alguém apareça
            for i in range(1, 5):
                tempo_teste = tempo_inicio + (passo * i)
                cap.set(cv2.CAP_PROP_POS_MSEC, tempo_teste * 1000)
                ret, frame = cap.read()
                
                if ret:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    # scaleFactor 1.1 e minNeighbors 4 deixam o radar mais sensível
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    
                    if len(faces) > 0:
                        cap.release()
                        # Encontra o maior rosto na tela (geralmente quem está com o foco da câmera)
                        maior_area = 0
                        melhor_x = None
                        for (x, y, w, h) in faces:
                            area = w * h
                            if area > maior_area:
                                maior_area = area
                                melhor_x = x + (w / 2)
                        
                        return melhor_x # Retorna o centro do alvo principal
            cap.release()
        except Exception as e:
            print(f"⚠️ Alerta no radar visual: {e}")
        return None 

    def analisar_com_llama(self, transcricao_str, ai_brain):
        print("🧠 [CÉREBRO]: Analisando roteiro e decidindo posicionamento tático...")
        prompt = f"""<|im_start|>system
Você é um editor de vídeos virais. Analise a transcrição e defina os cortes e o melhor posicionamento da legenda.
Regra 1: Escolha de 2 a 4 trechos (total 60-180s).
Regra 2: Determine o campo 'position' (0 a 100). Use 20 para base (padrão), 50 para centro ou 80 para topo, baseado na ênfase do texto.
Responda APENAS com JSON. Exemplo: {{"cortes": [{{"start": 10, "end": 70}}], "position": 25}}<|im_end|>
<|im_start|>user
{transcricao_str}<|im_end|>
<|im_start|>assistant
"""
        stream = ai_brain(prompt, max_tokens=300, stop=["<|im_end|>"], temperature=0.3)
        resposta = stream["choices"][0]["text"].strip()
        
        match = re.search(r'\{.*?\}', resposta, re.DOTALL)
        if match:
            try:
                dados = json.loads(match.group(0))
                # Retorna a lista de cortes e a posição sugerida pela IA
                return dados.get("cortes", [{"start": 10, "end": 70}]), dados.get("position", 20)
            except: pass
        return [{"start": 10, "end": 70}], 20

    def processar_alvo(self, config, ai_brain=None, callback=None):
        def log(msg):
            print(msg)
            if callback:
                try: callback(msg)
                except Exception: pass

        url = config.get("url")
        cor = config.get("color", "#ffffff")
        tamanho = int(config.get("size", 24)) * 2 
        estilo = config.get("style", "outline")
        sub_enabled = config.get("active", True) # Nova flag: Ativar ou não legenda
        auto_pos = config.get("autoPos", True)   # Nova flag: Posição automática
        
        log(f"📥 <b>[Fase 1/5] Infiltração:</b> Baixando alvo...")
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': f'{self.temp_dir}/alvo_%(id)s.%(ext)s',
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)

        log("🎧 <b>[Fase 2/5] Interrogatório:</b> Transcrevendo áudio com Whisper...")
        resultado = self.whisper_model.transcribe(video_path, fp16=False)

        transcricao_str = ""
        for seg in resultado["segments"]:
            transcricao_str += f"[{seg['start']:.1f} - {seg['end']:.1f}] {seg['text']}\n"

        limite_tatico = 7500 # Mantido para não explodir a VRAM
        if len(transcricao_str) > limite_tatico:
            log("⚠️ <b>[BLINDAGEM]:</b> Alvo massivo detectado. Fatiando texto...")
            transcricao_str = transcricao_str[:limite_tatico] + "\n...[FIM DE LEITURA SEGURA]"

        if ai_brain:
            log("🧠 <b>[Fase 3/5] Decisão:</b> LLaMA calculando clímax e posicionamento...")
            cortes, pos_sugerida = self.analisar_com_llama(transcricao_str, ai_brain)
            # Se o usuário escolheu "Auto", usamos o que a IA decidiu
            y_final = pos_sugerida if auto_pos else config.get("pos", 20)
            msg_cortes = ", ".join([f"({c['start']:.0f}s - {c['end']:.0f}s)" for c in cortes])
            log(f"✅ <b>[IA Decidiu]:</b> {len(cortes)} cortes. Posicionamento Vertical: {y_final}%")
        else:
            cortes = [{"start": 10.0, "end": 70.0}]
            y_final = config.get("pos", 20)

        log("🎯 <b>[Fase 4/5] Auto-Framing e Legendas em Lote...</b>")
        video_original = VideoFileClip(video_path)
        duracao_total_video = video_original.duration
        
        cor_fundo = "black" if estilo == "box" else "transparent"
        cor_texto = "yellow" if estilo == "yellow" else cor

        clipes_finais = []
        
        # ── O MOTOR DE COSTURA: Processa cada pedaço individualmente ──
        for idx, corte in enumerate(cortes):
            st = min(corte["start"], duracao_total_video - 1)
            nd = min(corte["end"], duracao_total_video)
            if st >= nd: continue

            log(f"✂️ Processando pedaço {idx+1}/{len(cortes)}...")
            subclip = video_original.subclip(st, nd)
            
            # Enquadra o rosto neste pedaço específico
            # O radar agora recebe o tempo de início e fim para vasculhar a área inteira
            centro_rosto_x = self.detectar_rosto_x(video_path, st, nd)
            w, h = subclip.size
            target_w = int(h * 9/16)
            
            x_center = centro_rosto_x if centro_rosto_x else (w / 2)
            if x_center - target_w/2 < 0: x_center = target_w/2
            if x_center + target_w/2 > w: x_center = w - target_w/2

            subclip = subclip.crop(x1=x_center - target_w/2, y1=0, x2=x_center + target_w/2, y2=h)
            y_pixels = subclip.h - (subclip.h * (int(y_final) / 100))

            # Cria legendas apenas para quem falou neste pedaço de tempo
            legendas_clips = []
            if sub_enabled: # Só gera os blocos de texto se estiver ativado no painel
                for segmento in resultado["segments"]:
                    seg_start = segmento["start"]
                    seg_end = segmento["end"]
                    texto_frase = segmento["text"].strip().upper()

                    if seg_end > st and seg_start < nd:
                        clip_start = max(0, seg_start - st)
                        clip_end = min(subclip.duration, seg_end - st)

                        txt_clip = TextClip(
                            texto_frase, fontsize=tamanho, color=cor_texto, bg_color=cor_fundo,
                            font="Arial", method='caption', size=(int(subclip.w * 0.85), None)
                        ).set_position(('center', y_pixels)).set_start(clip_start).set_end(clip_end).crossfadein(0.15).crossfadeout(0.15)
                        legendas_clips.append(txt_clip)

            if legendas_clips:
                clipes_finais.append(CompositeVideoClip([subclip] + legendas_clips))
            else:
                clipes_finais.append(subclip)

        log(f"🔥 <b>[Fase 5/5] Fusão Final:</b> Fundindo {len(clipes_finais)} cortes em um único arquivo viral...")
        nome_saida = f"corte_viral_costurado_{int(time.time())}.mp4"
        caminho_final = os.path.join(self.out_dir, nome_saida)
        
        final_video = None
        try:
            # Cola todos os pedaços juntos na ordem (method="compose" garante sincronia de áudio entre saltos)
            final_video = concatenate_videoclips(clipes_finais, method="compose")
            final_video.write_videofile(caminho_final, codec="libx264", audio_codec="aac", fps=30, preset="ultrafast")
            log(f"✅ <b>[MISSÃO CUMPRIDA]:</b> Clipe Dinâmico forjado e pronto para decolar!")
            return f"/static/media/{nome_saida}"
        except Exception as e:
            log(f"❌ <b>[ERRO DE RENDERIZAÇÃO]:</b> {e}")
            return None
        finally:
            try: video_original.close()
            except Exception: pass
            try: 
                if final_video: final_video.close()
            except Exception: pass
            for c in clipes_finais: 
                try: c.close()
                except Exception: pass
            if os.path.exists(video_path):
                try: os.remove(video_path)
                except Exception: pass