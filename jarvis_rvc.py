# filename: jarvis_rvc.py
import os
import sys
import re
import time
import tempfile
import asyncio
import subprocess
import edge_tts
from pathlib import Path
from pydub import AudioSegment

RVC_ROOT = r"c:\R2\models\Retrieval-based-Voice-Conversion-WebUI"
MODELO_PATH = os.path.join(RVC_ROOT, "assets", "weights", "jarvis.pth")

# Garante caminhos absolutos a partir de onde este script está rodando
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = BASE_DIR / "static" / "output" / "audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AUX_SCRIPT = os.path.join(BASE_DIR, "rvc_convert.py")

async def gerar_tts_base(texto: str, saida_mp3: str):
    communicate = edge_tts.Communicate(texto, "pt-BR-AntonioNeural")
    await communicate.save(saida_mp3)

async def sintetizar_jarvis(texto: str) -> str:
    texto = re.sub(r'```[\s\S]*?```', 'bloco de código omitido.', texto)
    texto = re.sub(r'[*_`#~>]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
        mp3_path = tmp_mp3.name
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
        wav_path = tmp_wav.name

    try:
        await gerar_tts_base(texto, mp3_path)
        audio = AudioSegment.from_file(mp3_path)
        audio.export(wav_path, format="wav")

        timestamp = int(time.time())
        out_filename = f"jarvis_{timestamp}.wav"
        out_path = OUTPUT_DIR / out_filename

        # [CORREÇÃO CRÍTICA APLICADA AQUI]
        # str(out_path.resolve()) força um caminho absoluto (C:\R2\static\...)
        # cwd=RVC_ROOT transporta a execução para dentro da pasta do modelo
        proc = await asyncio.create_subprocess_exec(
            sys.executable, AUX_SCRIPT, wav_path, str(out_path.resolve()), MODELO_PATH,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=RVC_ROOT 
        )
        
        try:
            # Espera até 30 segundos pela conversão
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError("Conversão do Jarvis demorou demais (Timeout)")
        
        if proc.returncode != 0:
            raise RuntimeError(f"Falha no rvc_convert: {stderr.decode()}")

        return f"/static/output/audio/{out_filename}"
    finally:
        for f in [mp3_path, wav_path]:
            try: os.unlink(f)
            except: pass