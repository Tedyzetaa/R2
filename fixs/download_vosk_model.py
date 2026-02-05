# download_vosk_model.py
import requests
import zipfile
import os
from pathlib import Path

def download_vosk_model():
    print("Baixando modelo VOSK para português...")
    
    # URL do modelo pequeno em português
    url = "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"
    model_dir = Path("models/vosk-model-small-pt-0.3")
    
    # Criar diretório se não existir
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Verificar se já existe
    if (model_dir / "README").exists():
        print("Modelo já existe!")
        return True
    
    try:
        # Baixar o arquivo
        print(f"Baixando de {url}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Salvar arquivo temporário
        zip_path = Path("vosk-model-small-pt-0.3.zip")
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extrair
        print("Extraindo...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("models/")
        
        # Limpar
        zip_path.unlink()
        
        print(f"✅ Modelo VOSK baixado para {model_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao baixar modelo: {e}")
        return False

if __name__ == "__main__":
    download_vosk_model()