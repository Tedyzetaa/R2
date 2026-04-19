# filename: video_ops.py
import os
import json
import re
import subprocess
from pathlib import Path

class VideoSurgeon:
    def __init__(self):
        self.output_dir = Path("static/media/cortes_virais")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print("✂️ [TESOURA NEURAL V4]: Córtex Viral Inicializado.")

    def extrair_audio(self, video_path, audio_path="temp_audio.wav"):
        print(f"🎙️ Extraindo áudio de {video_path}...")
        # FFmpeg extrai o áudio rapidamente sem perda de sincronia
        cmd = f'ffmpeg -y -i "{video_path}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{audio_path}"'
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return audio_path

    def transcrever_audio(self, audio_path):
        try:
            import whisper
            import warnings
            warnings.filterwarnings("ignore")
            print("🧠 Carregando modelo Whisper (Base) para transcrição...")
            # Usamos o modelo 'base' para ser rápido e não consumir toda a VRAM junto com o LLaMA
            model = whisper.load_model("base") 
            result = model.transcribe(audio_path)
            return result["segments"]
        except ImportError:
            return "ERRO_WHISPER"

    def analisar_cortes_com_ia(self, transcricao_segments, ai_brain):
        print("🤖 Analisando potencial viral com LLaMA...")
        
        texto_formatado = ""
        for seg in transcricao_segments:
            texto_formatado += f"[{seg['start']:.1f}s - {seg['end']:.1f}s]: {seg['text']}\n"

        sys_prompt = "Você é um Diretor de Corte Viral de elite. Analise a transcrição de vídeo abaixo e identifique os 3 a 5 momentos mais engajadores, polêmicos ou interessantes (com início e fim precisos em segundos). Retorne APENAS um array JSON válido, sem explicações."
        
        exemplo_json = '''[
    {"tema": "A grande revelacao", "start": 12.5, "end": 45.0, "motivo": "Gera curiosidade no inicio"},
    {"tema": "Dica pratica absurda", "start": 60.0, "end": 90.0, "motivo": "Entrega valor imediato"}
]'''

        prompt = f"<|im_start|>system\n{sys_prompt}\nExemplo de saída obrigatória:\n{exemplo_json}<|im_end|>\n<|im_start|>user\nTranscrição:\n{texto_formatado}<|im_end|>\n<|im_start|>assistant\n"

        resp = ""
        for chunk in ai_brain(prompt, max_tokens=2048, stop=["<|im_end|>"], stream=True):
            resp += chunk["choices"][0]["text"]

        try:
            # Caça o JSON no meio da resposta da IA
            match = re.search(r'\[.*\]', resp, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception as e:
            print(f"Erro no parse do JSON: {e}")
        return None

    def executar_cortes(self, video_path, cortes):
        arquivos_gerados = []
        for i, corte in enumerate(cortes):
            tema_limpo = re.sub(r'[^a-zA-Z0-9]', '_', corte.get('tema', f'corte_{i}')).lower()
            out_path = self.output_dir / f"viral_{i}_{tema_limpo}.mp4"
            
            start = float(corte['start'])
            end = float(corte['end'])
            duracao = end - start
            
            print(f"✂️ Forjando corte: {tema_limpo} ({start}s até {end}s)")
            # Recodificação ultrafast para entregar rápido
            cmd = f'ffmpeg -y -i "{video_path}" -ss {start} -t {duracao} -c:v libx264 -preset ultrafast -c:a aac "{out_path}"'
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            arquivos_gerados.append(str(out_path))
        
        return arquivos_gerados

    def processar_video_viral(self, video_path, ai_brain):
        if not os.path.exists(video_path): 
            return f"❌ Alvo não encontrado: {video_path}"
        
        audio = self.extrair_audio(video_path)
        
        segments = self.transcrever_audio(audio)
        if segments == "ERRO_WHISPER":
            return "❌ Comando falhou. Instale o Whisper no Conda executando: pip install openai-whisper"
            
        cortes_planejados = self.analisar_cortes_com_ia(segments, ai_brain)
        
        if not cortes_planejados:
            return "❌ O Cérebro LLaMA falhou em estruturar os cortes virais (JSON corrompido). Tente novamente."

        arquivos = self.executar_cortes(video_path, cortes_planejados)
        
        # Limpa rastros
        if os.path.exists(audio): os.remove(audio)
            
        return arquivos