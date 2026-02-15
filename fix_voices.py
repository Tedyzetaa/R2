import os
import urllib.request
import sys

print("🔄 Trocando sistema de vozes para formato BINÁRIO (Pickle)...")

# URLs oficiais
bin_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.bin"
json_path = "models/voices.json"
bin_path = "models/voices.bin"

# 1. Remove o JSON antigo (para não confundir)
if os.path.exists(json_path):
    print(f"🗑️ Removendo {json_path}...")
    os.remove(json_path)

# 2. Baixa o BIN
print(f"⬇️ Baixando {bin_path}...")
try:
    urllib.request.urlretrieve(bin_url, bin_path)
    print("✅ Download concluído!")
except Exception as e:
    print(f"❌ Erro no download: {e}")
    sys.exit(1)