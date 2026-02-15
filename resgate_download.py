import os
import urllib.request
import sys

print("🇧🇷 INICIANDO PROTOCOLO DE RESGATE (Fonte: HuggingFace)...")

# URLs Oficiais do Repositório onnx-community
BASE_URL = "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/"

files = {
    # Nome no Servidor -> Nome Local
    "voices.json": "voices-v1.0.json", 
    "kokoro-v1.0.onnx": "kokoro-v1.0.onnx"
}

if not os.path.exists("models"):
    os.makedirs("models")

# Configura o 'User-Agent' para o HuggingFace não bloquear o script
opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')]
urllib.request.install_opener(opener)

for remote_name, local_name in files.items():
    url = BASE_URL + remote_name
    save_path = os.path.join("models", local_name)
    
    # Se o arquivo de modelo pesado já existe, pula
    if local_name == "kokoro-v1.0.onnx" and os.path.exists(save_path):
        print(f"✅ {local_name} já existe. Pulando download pesado.")
        continue

    print(f"⬇️ Baixando {remote_name} (Salvo como {local_name})...")
    try:
        urllib.request.urlretrieve(url, save_path)
        print(f"✅ Download concluído: {local_name}")
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")
        # Se falhar aqui, é problema de conexão ou o site caiu
        sys.exit(1)

print("\n🚀 ARQUIVOS DE VOZ BRASILEIRA RECUPERADOS.")