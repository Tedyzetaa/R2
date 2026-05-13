# rvc_infer.py
import sys
import os
import numpy as np
import torch
from pathlib import Path

# Configuração do ambiente RVC
RVC_ROOT = r"c:\R2\models\Retrieval-based-Voice-Conversion-WebUI"
sys.path.insert(0, RVC_ROOT)
sys.path.insert(0, os.path.join(RVC_ROOT, "infer"))

from infer.modules.vc.modules import VC
from infer.lib.audio import load_audio, wav2

class DummyConfig:
    def __init__(self):
        self.device = "cpu"
        self.is_half = False
        self.gpu_id = 0
        self.hub = None
        self.f0_method = "rmvpe"

def main():
    # Recebe argumentos: entrada_wav, saida_wav, modelo_path
    if len(sys.argv) != 4:
        print("Uso: rvc_infer.py <entrada.wav> <saida.wav> <modelo.pth>")
        sys.exit(1)
    entrada = sys.argv[1]
    saida = sys.argv[2]
    modelo = sys.argv[3]

    config = DummyConfig()
    vc = VC(config)
    # Carrega o modelo: o método get_vc espera um sid e depois argumentos variádicos.
    # Tentamos passar o modelo como argumento posicional após o sid.
    try:
        # Algumas versões aceitam vc.get_vc(sid, model_path)
        vc.get_vc(0, modelo)
    except:
        # Fallback: tenta vc.load_model(modelo)
        vc.load_model(modelo)
    audio_data = load_audio(entrada, 16000)
    audio_data = audio_data / np.max(np.abs(audio_data))
    converted = vc.vc_single(
        0, audio_data,
        f0_up_key=0,
        index_rate=0.6,
        protect=0.33,
        f0_method="rmvpe",
        resample_sr=0,
        rms_mix_rate=0.25
    )
    wav2(converted, saida, 16000)

if __name__ == "__main__":
    main()