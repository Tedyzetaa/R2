import os
import urllib.request
import sys

print("🇧🇷 INICIANDO ATUALIZAÇÃO PARA PROTOCOLO BRASIL (v1.0)...")

# URLs Oficiais do Kokoro v1.0 (Suporte PT-BR Nativo)
# Fonte: https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/
base_url = "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/"

files = {
    "kokoro-v1.0.onnx": "onnx/model.onnx", # O modelo v1.0 renomeado para facilitar
    "voices-v1.0.bin": "voices.bin"        # O arquivo de vozes v1.0
}

if not os.path.exists("models"):
    os.makedirs("models")

for local_name, remote_name in files.items():
    path = os.path.join("models", local_name)
    url = base_url + remote_name
    
    print(f"⬇️ Baixando {local_name}...")
    try:
        # User-Agent é necessário para o HuggingFace não bloquear o script
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        
        urllib.request.urlretrieve(url, path)
        print(f"✅ {local_name} instalado.")
    except Exception as e:
        print(f"❌ Erro ao baixar {local_name}: {e}")
        # Tenta URL alternativa direta se falhar
        if local_name == "voices-v1.0.bin":
             alt_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices.bin"
             print(f"🔄 Tentando espelho alternativo para vozes...")
             urllib.request.urlretrieve(alt_url, path)

print("\n🚀 ATUALIZAÇÃO CONCLUÍDA. AGORA VOCÊ TEM VOZES NATIVAS.")