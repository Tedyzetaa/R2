import os
import requests
from pathlib import Path

def download_file(url, destination):
    print(f"[*] Tentando baixar de: {url}")
    try:
        response = requests.get(url, stream=True, timeout=15)
        if response.status_code == 200:
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[+] Sucesso! Arquivo salvo em: {destination}")
            return True
        else:
            print(f"[!] Erro {response.status_code} para este link.")
            return False
    except Exception as e:
        print(f"[!] Falha na conexão: {e}")
        return False

def main():
    # Estrutura de pastas baseada no seu diretório R2
    base_path = Path(r"c:\R2\models\Retrieval-based-Voice-Conversion-WebUI")
    weights_dir = base_path / "assets" / "weights"
    index_dir = base_path / "logs" / "jarvis"

    weights_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    # Lista de possíveis URLs para o arquivo .pth (Hugging Face é sensível a Case)
    pth_targets = [
        "https://huggingface.co/jgkawell/jarvis/resolve/main/jarvis.pth",
        "https://huggingface.co/jgkawell/jarvis/resolve/main/Jarvis.pth"
    ]
    
    index_url = "https://huggingface.co/jgkawell/jarvis/resolve/main/added_IVF161_Flat_nprobe_1_jarvis_v2.index"

    # Tentando baixar o .pth
    success_pth = False
    for url in pth_targets:
        if download_file(url, weights_dir / "jarvis.pth"):
            success_pth = True
            break
    
    if not success_pth:
        print("\n[!] Não foi possível encontrar o arquivo .pth automaticamente.")
        print(f"Por favor, baixe manualmente em: https://huggingface.co/jgkawell/jarvis/tree/main")
        print(f"E coloque em: {weights_dir}")

    # Baixando o .index
    download_file(index_url, index_dir / "jarvis.index")

    if success_pth:
        print("\n" + "="*50)
        print("SISTEMA JARVIS INTEGRADO AO R2 TACTICAL OS")
        print("="*50)

if __name__ == "__main__":
    main()