import os
import urllib.request
import sys

print("🇧🇷 ROTA DE RECUPERAÇÃO: BAIXANDO ARQUIVOS v1.0 (JSON)...")

# Links diretos do Release v1.0 (Estáveis)
base_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
files = {
    "kokoro-v1.0.onnx": "kokoro-v1.0.onnx",
    "voices-v1.0.json": "voices.json" # Salvando como voices-v1.0.json para organizar
}

if not os.path.exists("models"):
    os.makedirs("models")

# Limpeza preventiva de arquivos corrompidos ou antigos
for f in ["models/voices-v1.0.bin", "models/voices.bin"]:
    if os.path.exists(f):
        print(f"🗑️ Removendo arquivo obsoleto: {f}")
        os.remove(f)

for remote_name, local_name in files.items():
    url = base_url + remote_name
    save_path = os.path.join("models", local_name)
    
    print(f"⬇️ Baixando {local_name}...")
    try:
        urllib.request.urlretrieve(url, save_path)
        print(f"✅ {local_name} baixado com sucesso!")
    except Exception as e:
        print(f"❌ Falha crítica ao baixar {local_name}: {e}")
        sys.exit(1)

print("\n🚀 DOWNLOAD CONCLUÍDO. PROTOCOLO JSON ATIVO.")