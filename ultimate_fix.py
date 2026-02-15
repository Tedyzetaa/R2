import os
import urllib.request
import sys

print("🇧🇷 INICIANDO PROTOCOLO ULTIMATE FIX...")

# URL Oficial do Criador (Hexgrad) - Fonte da Verdade
# Esse arquivo contém TODAS as vozes v1.0 (incluindo BR)
URL_VOICES = "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices.json"
URL_MODEL = "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/onnx/model.onnx"

DEST_VOICES = "models/voices-v1.0.json"
DEST_MODEL = "models/kokoro-v1.0.onnx"

if not os.path.exists("models"):
    os.makedirs("models")

def download_with_fallback(url, path, description):
    print(f"⬇️ Baixando {description}...")
    try:
        # Headers para fingir ser um navegador (evita bloqueio 403/404)
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        
        urllib.request.urlretrieve(url, path)
        print(f"✅ {description} baixado: {path}")
    except Exception as e:
        print(f"❌ FALHA AUTOMÁTICA EM {description}: {e}")
        print(f"⚠️ AÇÃO MANUAL NECESSÁRIA:")
        print(f"1. Baixe este arquivo no navegador: {url}")
        print(f"2. Salve na pasta 'models' com o nome: {os.path.basename(path)}")
        # Não mata o script, tenta baixar o próximo

# 1. Baixar o JSON de Vozes (O crítico)
download_with_fallback(URL_VOICES, DEST_VOICES, "Vozes Brasileiras (voices.json)")

# 2. Baixar o Modelo ONNX (Se não tiver)
if not os.path.exists(DEST_MODEL):
    download_with_fallback(URL_MODEL, DEST_MODEL, "Modelo Neural v1.0")
else:
    print("✅ Modelo Neural já existe.")

print("\n🏁 EXECUÇÃO FINALIZADA. VERIFIQUE SE NÃO HOUVE ERROS.")teste_manual