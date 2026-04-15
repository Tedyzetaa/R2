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
        print("✂️ [TESOURA NEURAL - MODO NUVEM]: Inicializando Córtex de Costura Dinâmica...")
        self.whisper_model = whisper.load_model("base")
        self.temp_dir = "temp_video"
        self.out_dir = "static/media"
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.out_dir, exist_ok=True)

    def detectar_rosto_x(self, video_path, tempo_alvo):
        """Olho de Águia (OpenCV)"""
        try:
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_MSEC, tempo_alvo * 1000)
            ret, frame = cap.read()
            cap.release()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                if len(faces) > 0:
                    (x, y, w, h) = faces[0]
                    return x + (w / 2)
        except Exception:
            pass
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
        sub_enabled = config.get("active", True)
        auto_pos = config.get("autoPos", True)
        
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

        limite_tatico = 7500
        if len(transcricao_str) > limite_tatico:
            log("⚠️ <b>[BLINDAGEM]:</b> Alvo massivo detectado. Fatiando texto...")
            transcricao_str = transcricao_str[:limite_tatico] + "\n...[FIM DE LEITURA SEGURA]"

        if ai_brain:
            log("🧠 <b>[Fase 3/5] Decisão:</b> LLaMA calculando clímax e posicionamento...")
            cortes, pos_sugerida = self.analisar_com_llama(transcricao_str, ai_brain)
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
        
        for idx, corte in enumerate(cortes):
            st = min(corte["start"], duracao_total_video - 1)
            nd = min(corte["end"], duracao_total_video)
            if st >= nd: continue

            log(f"✂️ Processando pedaço {idx+1}/{len(cortes)}...")
            subclip = video_original.subclip(st, nd)
            
            centro_rosto_x = self.detectar_rosto_x(video_path, st + min(3, (nd-st)/2))
            w, h = subclip.size
            target_w = int(h * 9/16)
            
            x_center = centro_rosto_x if centro_rosto_x else (w / 2)
            if x_center - target_w/2 < 0: x_center = target_w/2
            if x_center + target_w/2 > w: x_center = w - target_w/2

            subclip = subclip.crop(x1=x_center - target_w/2, y1=0, x2=x_center + target_w/2, y2=h)
            y_pixels = subclip.h - (subclip.h * (int(y_final) / 100))

            legendas_clips = []
            if sub_enabled:
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