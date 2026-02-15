import os
import json

path = "models/voices.json"

print(f"🔍 Analisando: {path}")

if not os.path.exists(path):
    print("❌ Arquivo não encontrado!")
else:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read(100) # Lê os primeiros 100 caracteres
            print(f"\n📄 Conteúdo inicial:\n{content}")
            
            if content.strip().startswith("{"):
                print("\n✅ O arquivo parece um JSON válido.")
            else:
                print("\n❌ O arquivo NÃO parece um JSON (pode estar corrompido).")
    except Exception as e:
        print(f"\n❌ Erro ao ler arquivo: {e}")

print("\n📦 Testando importação da biblioteca:")
try:
    import kokoro_onnx
    print(f"✅ Versão instalada: {kokoro_onnx.__version__ if hasattr(kokoro_onnx, '__version__') else 'Desconhecida'}")
except ImportError:
    print("❌ Biblioteca kokoro-onnx não encontrada.")fix_voices