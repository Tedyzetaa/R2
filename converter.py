import json
import pickle
import os
import numpy as np

print("🔄 INICIANDO CONVERSÃO DE PROTOCOLO DE VOZ...")

# Caminhos
INPUT_JSON = "models/voices-v1.0.json"
OUTPUT_BIN = "models/voices_fixed.bin"

# 1. Verifica se o JSON existe
if not os.path.exists(INPUT_JSON):
    # Tenta achar com o nome antigo caso tenha salvo diferente
    if os.path.exists("models/voices.json"):
        INPUT_JSON = "models/voices.json"
    else:
        print("❌ ERRO: Não encontrei 'models/voices-v1.0.json'.")
        print("Certifique-se que você baixou o arquivo manualmente e colocou na pasta models!")
        exit()

try:
    # 2. Lê o arquivo de texto (JSON)
    print(f"📖 Lendo dados de: {INPUT_JSON}")
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    # 3. Verifica se a DORA está lá
    if "pf_dora" in dados:
        print("✅ Voz feminina 'pf_dora' detectada no pacote.")
    else:
        print("⚠️ AVISO: Voz 'pf_dora' não encontrada. Verifique se baixou a versão v1.0.")

    # 4. Salva como Binário (Pickle) que o seu Numpy aceita
    print(f"💾 Salvando binário compatível: {OUTPUT_BIN}")
    with open(OUTPUT_BIN, 'wb') as f:
        pickle.dump(dados, f)
        
    print("\n🚀 CONVERSÃO BEM SUCEDIDA!")
    print("O arquivo 'voices_fixed.bin' foi criado e está pronto para uso.")

except Exception as e:
    print(f"❌ Falha na conversão: {e}")