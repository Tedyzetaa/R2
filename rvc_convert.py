# filename: rvc_convert.py
import os
import sys
import argparse
import torch
import numpy as np

# --- PATCH DE SEGURANÇA E AMBIENTE ---
# Permite carregar o Hubert no PyTorch 2.6+
try:
    import fairseq
    torch.serialization.add_safe_globals([fairseq.data.dictionary.Dictionary])
except:
    pass

# Força o PyTorch a aceitar os pesos se o add_safe_globals falhar
torch.serialization.weights_only = False 

# Configuração de Caminhos Absolutos
RVC_ROOT = r"c:\R2\models\Retrieval-based-Voice-Conversion-WebUI"
# Injeta as variáveis que o pipeline do RVC exige internamente
os.environ["rmvpe_root"] = os.path.join(RVC_ROOT, "assets", "rmvpe")
os.environ["weight_root"] = os.path.join(RVC_ROOT, "assets", "weights")
os.environ["index_root"] = os.path.join(RVC_ROOT, "assets", "weights")

sys.path.insert(0, RVC_ROOT)

from infer.modules.vc.modules import VC
from infer.lib.audio import load_audio, wav2

class Config:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_half = True if self.device == "cuda" else False
        self.gpu_id = 0
        self.f0_method = "rmvpe"
        self.x_pad = 3
        self.x_query = 10
        self.x_center = 60
        self.x_max = 100
        self.version = "v2"
        self.hubert_path = os.path.join(RVC_ROOT, "assets", "hubert", "hubert_base.pt")
        self.rmvpe_path = os.path.join(RVC_ROOT, "assets", "rmvpe", "rmvpe.pt")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="WAV de entrada")
    parser.add_argument("output", help="WAV de saída")
    parser.add_argument("model", help="Caminho do .pth")
    args = parser.parse_args()

    cfg = Config()
    vc = VC(cfg)
    
    # Carrega o modelo do Jarvis
    model_name = os.path.basename(args.model)
    vc.get_vc(model_name)

    try:
        # Conversão com os parâmetros táticos do Jarvis
        info, (tgt_sr, audio_opt) = vc.vc_single(
            sid=0, 
            input_audio_path=args.input,
            f0_up_key=0, # Ajuste para -12 se a voz original for feminina e quiser o Jarvis grave
            f0_file=None,
            f0_method="rmvpe", # Se travar, mude para "pm" (muito mais rápido, menos qualidade)
            file_index="", 
            file_index2="",
            index_rate=0.5,     # Reduzido de 0.75 para poupar memória
            filter_radius=3,
            resample_sr=0,
            rms_mix_rate=0.25,
            protect=0.33
        )
        wav2(audio_opt, args.output, tgt_sr)
        print("SUCCESS")
    except Exception as e:
        print(f"ERRO_CONVERSAO: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()