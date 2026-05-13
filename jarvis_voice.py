# filename: jarvis_voice.py
import os
import sys
import subprocess
import tempfile
import asyncio
import edge_tts
from pathlib import Path

# Configuração dos caminhos do RVC
RVC_ROOT = r"c:\R2\models\Retrieval-based-Voice-Conversion-WebUI"
RVC_INFER_SCRIPT = os.path.join(RVC_ROOT, "infer-web.py")
RVC_WEIGHTS_DIR = os.path.join(RVC_ROOT, "assets", "weights")
RVC_INDEX_DIR = os.path.join(RVC_ROOT, "logs", "jarvis_v2")

# Nome do modelo Jarvis (sem extensão)
JARVIS_MODEL = "jarvis_v2"   # deve existir jarvis_v2.pth
JARVIS_INDEX = "jarvis_v2"   # deve existir jarvis_v2.index (opcional)

# Pasta de saída
OUTPUT_DIR = Path("static/output/audio")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def obter_caminho_modelo() -> str:
    """Retorna o caminho completo do arquivo .pth do modelo Jarvis."""
    pth_path = os.path.join(RVC_WEIGHTS_DIR, f"{JARVIS_MODEL}.pth")
    if not os.path.exists(pth_path):
        # Tenta busca recursiva
        for root, dirs, files in os.walk(RVC_ROOT):
            for file in files:
                if file.endswith(".pth") and JARVIS_MODEL in file.lower():
                    return os.path.join(root, file)
        raise FileNotFoundError(f"Modelo {JARVIS_MODEL}.pth não encontrado em {RVC_WEIGHTS_DIR}")
    return pth_path


def obter_caminho_indice() -> str:
    """Retorna o caminho do arquivo .index do modelo Jarvis (se existir)."""
    index_path = os.path.join(RVC_INDEX_DIR, f"{JARVIS_INDEX}.index")
    if not os.path.exists(index_path):
        # Busca alternativa
        for root, dirs, files in os.walk(RVC_ROOT):
            for file in files:
                if file.endswith(".index") and JARVIS_INDEX in file.lower():
                    return os.path.join(root, file)
        return ""   # índice opcional
    return index_path


async def gerar_audio_base(texto: str, arquivo_saida: str) -> None:
    """Gera áudio base usando edge_tts (voz AntonioNeural)."""
    communicate = edge_tts.Communicate(texto, "pt-BR-AntonioNeural")
    await communicate.save(arquivo_saida)


def converter_com_rvc(entrada_wav: str, saida_wav: str) -> bool:
    """
    Converte o áudio de entrada usando o RVC via infer-web.py.
    Retorna True se bem-sucedido.
    """
    modelo_path = obter_caminho_modelo()
    index_path = obter_caminho_indice()

    # Parâmetros recomendados para o Jarvis (tom natural, PT-BR)
    cmd = [
        sys.executable,
        RVC_INFER_SCRIPT,
        "--model_path", modelo_path,
        "--input_file", entrada_wav,
        "--output_file", saida_wav,
        "--f0_up_key", "0",           # sem transposição
        "--index_rate", "0.6",        # equilibrio timbre/entonação
        "--protect", "0.33",
        "--rms_mix_rate", "0.25",
        "--f0_method", "rmvpe",
        "--index_path", index_path if index_path else "",
    ]
    # Remove argumento vazio
    cmd = [arg for arg in cmd if arg]

    try:
        # Executa e aguarda conclusão
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return True
        else:
            print(f"Erro RVC: {result.stderr}")
            return False
    except Exception as e:
        print(f"Exceção ao executar RVC: {e}")
        return False


async def sintetizar_jarvis(texto: str) -> str:
    """
    Pipeline completo:
    1. Gera áudio base (TTS) em arquivo temporário.
    2. Converte via RVC para o timbre Jarvis.
    3. Salva o resultado final em static/output/audio/jarvis_<timestamp>.wav
    4. Retorna o caminho URL (ex: /static/output/audio/jarvis_xxx.wav)
    """
    # Remove markdown/símbolos antes de falar (opcional)
    texto_limpo = texto.replace("```", "").replace("*", "").strip()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_entrada:
        input_path = tmp_entrada.name

    # 1. Gerar TTS base (edge_tts salva como mp3, mas o RVC prefere wav)
    mp3_temp = input_path.replace(".wav", ".mp3")
    await gerar_audio_base(texto_limpo, mp3_temp)

    # Converter mp3 para wav (usando ffmpeg, se disponível)
    # Se não tiver ffmpeg, podemos usar pydub (mas evitemos dependências)
    # Vamos usar o próprio edge_tts para gerar wav? Ele não suporta. 
    # Alternativa: usar pydub (já está no projeto) para converter.
    from pydub import AudioSegment
    audio = AudioSegment.from_file(mp3_temp)
    audio.export(input_path, format="wav")

    # 2. Preparar saída final
    import time
    timestamp = int(time.time())
    output_filename = f"jarvis_{timestamp}.wav"
    output_path = OUTPUT_DIR / output_filename

    # 3. Chamar RVC
    sucesso = converter_com_rvc(input_path, str(output_path))

    # Limpeza
    for f in [mp3_temp, input_path]:
        try:
            os.unlink(f)
        except:
            pass

    if sucesso and os.path.exists(output_path):
        return f"/static/output/audio/{output_filename}"
    else:
        raise RuntimeError("Falha na conversão RVC")


# Teste rápido (se executar diretamente)
if __name__ == "__main__":
    async def test():
        url = await sintetizar_jarvis("Olá, eu sou o Jarvis, seu assistente tático.")
        print(f"Áudio gerado: {url}")
    asyncio.run(test())