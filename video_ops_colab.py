# filename: video_ops_colab.py
import os
import json
import tempfile
import subprocess
import gc
import re
import torch

class VideoSurgeon:
    def __init__(self):
        print("✂️ [TESOURA NEURAL V4]: Córtex Viral Inicializado (Linux/Colab).")

    def processar_video_viral(self, video_path, ai_brain):
        # 1. INTERCEPTADOR DE YOUTUBE
        if video_path.startswith("http://") or video_path.startswith("https://"):
            try:
                import yt_dlp
            except ImportError:
                return "❌ Erro: yt-dlp não instalada. Execute: pip install yt-dlp"
            print(f"✂️ Baixando vídeo do YouTube...")
            media_dir = "/content/static/media"
            os.makedirs(media_dir, exist_ok=True)
            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(media_dir, 'temp_yt_%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_path, download=True)
                    video_path = ydl.prepare_filename(info)
                    print(f"✂️ Download concluído -> {video_path}")
            except Exception as e:
                return f"❌ Erro ao baixar: {str(e)}"
        elif not os.path.exists(video_path):
            return f"❌ Arquivo não encontrado: {video_path}"

        # 2. VALIDAÇÃO DO WHISPER
        try:
            import whisper
        except ImportError:
            return "❌ Whisper não instalado."

        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name

        try:
            # 3. Extração de áudio com ffmpeg (Linux)
            cmd_audio = f'ffmpeg -y -i "{video_path}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{temp_audio}"'
            subprocess.run(cmd_audio, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # 4. Transcrição
            print("✂️ Transcrevendo áudio...")
            model = whisper.load_model("base")
            result = model.transcribe(temp_audio)
            transcricao = result["text"]

            # 5. Limpeza de memória
            del model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # 6. LLM para cortes
            print("✂️ Analisando cortes virais...")
            sys_prompt = "Você é um Diretor de Corte Viral. Retorne APENAS um array JSON com cortes. Chaves: 'tema', 'start', 'end', 'motivo'. Formato de tempo HH:MM:SS."
            prompt = f"<|im_start|>system\n{sys_prompt}\n<|im_end|>\n<|im_start|>user\nTranscrição: {transcricao}\n<|im_end|>\n<|im_start|>assistant\n"
            resp = ai_brain(prompt, max_tokens=2048, stop=["<|im_end|>"])
            texto_ia = resp["choices"][0]["text"]

            match = re.search(r'\[[\s\S]*?\]', texto_ia)
            if not match:
                return f"❌ JSON não encontrado. Resposta: {texto_ia}"
            cortes = json.loads(match.group(0))

            # 7. Recortes com ffmpeg
            out_dir = "/content/static/media/cortes_virais"
            os.makedirs(out_dir, exist_ok=True)
            arquivos_gerados = []
            for i, c in enumerate(cortes):
                tema = re.sub(r'[^\w\-]', '_', c.get('tema', f'corte_viral_{i}'))
                t_start = c.get('start', '00:00:00')
                t_end = c.get('end', '00:00:15')
                out_file = os.path.join(out_dir, f"{tema}.mp4")
                cmd_cut = f'ffmpeg -y -ss {t_start} -i "{video_path}" -to {t_end} -preset ultrafast -c copy "{out_file}"'
                subprocess.run(cmd_cut, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                arquivos_gerados.append(out_file)
            return arquivos_gerados

        except Exception as e:
            return f"❌ Erro Crítico: {str(e)}"
        finally:
            if os.path.exists(temp_audio):
                os.unlink(temp_audio)