# filename: limpar_r2.py
import os
import shutil
from pathlib import Path

def expurgar_sistema():
    print("🧹 [R2] Iniciando Protocolo de Limpeza Total...")
    
    # Definição dos alvos (Caminhos relativos à raiz c:\r2)
    diretorios_limpeza = [
        "static/media",               # Cache de áudios r2_voice e temp_yt
        "static/media/cortes_virais", # Saídas da Tesoura Neural
        "temp_video",                 # Ficheiros de processamento temporário
        "__pycache__"                 # Cache de compilação do Python
    ]

    arquivos_deletados = 0
    pastas_limpas = 0

    for alvo in diretorios_limpeza:
        caminho = Path(alvo)
        
        if caminho.exists():
            print(f"📡 Varrendo: {alvo}...")
            # Para cada item dentro da pasta
            for item in caminho.iterdir():
                try:
                    if item.is_file():
                        # Mantemos apenas o .gitkeep se existir, para não quebrar a estrutura
                        if item.name != ".gitkeep":
                            item.unlink()
                            arquivos_deletados += 1
                    elif item.is_dir():
                        shutil.rmtree(item)
                        pastas_limpas += 1
                except Exception as e:
                    print(f"⚠️ Falha ao remover {item.name}: {e}")
        else:
            print(f"ℹ️ Alvo não encontrado ou já limpo: {alvo}")

    # Limpeza profunda de __pycache__ em subpastas
    for p in Path('.').rglob('__pycache__'):
        try:
            shutil.rmtree(p)
            pastas_limpas += 1
        except:
            pass

    print("\n" + "="*40)
    print(f"✅ [SUCESSO]: Sistema Higienizado!")
    print(f"🗑️ Arquivos removidos: {arquivos_deletados}")
    print(f"📂 Pastas removidas: {pastas_limpas}")
    print("="*40)

if __name__ == "__main__":
    # Confirmação de segurança
    confirmar = input("⚠️ Isso apagará todo o cache de voz e vídeos gerados. Prosseguir? (s/n): ")
    if confirmar.lower() == 's':
        expurgar_sistema()
    else:
        print("❌ Operação abortada pelo Comandante.")