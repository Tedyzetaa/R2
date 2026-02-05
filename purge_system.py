import os
import shutil

def limpar_sistema_silencioso():
    # Mesma lógica do limpar_sistema, mas sem o input() de confirmação
    # Retorna uma string com o resumo para o Telegram
    arquivos_vitais = ["force_sci_fi_gui.py", "config.json", ".env", "requirements.txt", "purge_system.py"]
    pastas_vitais = ["features", "assets", "logs"]
    extensoes_lixo = ['.gif', '.jpg', '.png', '.mp4', '.tmp', '.log']
    
    count_del = 0
    for item in os.listdir('.'):
        if item in arquivos_vitais or item in pastas_vitais: continue
        if any(item.endswith(ext) for ext in extensoes_lixo) or item.startswith('test_'):
            try:
                os.remove(item)
                count_del += 1
            except: pass
    return f"🧹 Saneamento concluído. {count_del} arquivos temporários removidos."

def limpar_sistema():
    relatorio = limpar_sistema_silencioso()
    print("\n" + "="*40)
    print(f"✅ VARREDURA CONCLUÍDA")
    print(relatorio)
    print("="*40)

if __name__ == "__main__":
    confirmacao = input("❗ Isso apagará arquivos temporários e de teste. Confirmar? (s/n): ")
    if confirmacao.lower() == 's':
        limpar_sistema()
    else:
        print("❌ Operação cancelada.")