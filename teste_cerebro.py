import os
import sys

print("╔══════════════════════════════════════╗")
print("║     DIAGNÓSTICO DE CÉREBRO LOCAL     ║")
print("╚══════════════════════════════════════╝")

# 1. VERIFICAÇÃO DE ARQUIVO
print("\n🔍 1. Verificando arquivo do modelo...")
# Caminho exato que você me passou
caminho_modelo = r"C:\R2\models\Meta-Llama-3-8B-Instruct.Q4_K_M.gguf"

if os.path.exists(caminho_modelo):
    tamanho = os.path.getsize(caminho_modelo) / (1024 * 1024 * 1024) # Em GB
    print(f"   ✅ Arquivo encontrado!")
    print(f"   📂 Tamanho: {tamanho:.2f} GB")
else:
    print(f"   ❌ ARQUIVO NÃO ENCONTRADO!")
    print(f"   O sistema procurou em: {caminho_modelo}")
    print("   Certifique-se de que a pasta se chama 'models' (minúsculo) e está na raiz C:\\R2")
    sys.exit()

# 2. VERIFICAÇÃO DE BIBLIOTECA
print("\n🔍 2. Importando Llama-cpp-python...")
try:
    from llama_cpp import Llama
    print("   ✅ Biblioteca importada com sucesso.")
except ImportError:
    print("   ❌ ERRO: Biblioteca não instalada.")
    sys.exit()
except Exception as e:
    print(f"   ❌ ERRO DE DLL/COMPATIBILIDADE: {e}")
    sys.exit()

# 3. TESTE DE CARGA (O Momento da Verdade)
print("\n🔍 3. Tentando carregar o modelo na RAM (Isso pode demorar)...")
try:
    # verbose=True vai mostrar o log interno do C++
    llm = Llama(
        model_path=caminho_modelo,
        n_ctx=2048,      # Reduzi um pouco para garantir que cabe na RAM
        n_gpu_layers=0,  # Força CPU para testar compatibilidade básica
        verbose=True 
    )
    print("   ✅ SUCESSO! O modelo carregou.")
except Exception as e:
    print(f"   ❌ FALHA NO CARREGAMENTO: {e}")
    print("   Dica: Se o erro for 'Memory', feche o Chrome e tente de novo.")
    sys.exit()

# 4. TESTE DE CONVERSA
print("\n🔍 4. Testando raciocínio...")
try:
    output = llm.create_chat_completion(
        messages=[{"role": "user", "content": "Responda apenas: Sistema Online."}],
        max_tokens=20
    )
    resposta = output['choices'][0]['message']['content']
    print(f"   🤖 R2 Respondeu: {resposta}")
except Exception as e:
    print(f"   ❌ Erro ao gerar texto: {e}")

print("\n🏁 DIAGNÓSTICO CONCLUÍDO.")