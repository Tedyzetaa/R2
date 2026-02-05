import os
import subprocess
import glob
import sys

def imprimir_status(texto):
    print(f"🔧 [MANUTENÇÃO]: {texto}")

def matar_processos_zumbis():
    imprimir_status("Eliminando processos Python/Chrome travados...")
    if os.name == 'nt': # Windows
        os.system("taskkill /f /im python.exe")
        os.system("taskkill /f /im chrome.exe")
        os.system("taskkill /f /im msedge.exe")
    else:
        os.system("pkill -9 python")
    imprimir_status("Memória limpa.")

def limpar_arquivos_temporarios():
    imprimir_status("Removendo imagens táticas antigas...")
    # Lista de padrões de arquivos gerados pelos módulos
    padroes = [
        "*.png",
        "*.jpg",
        "*.gif",
        "frames_temp/*" # Limpa a pasta de frames do timelapse
    ]
    
    contador = 0
    for padrao in padroes:
        arquivos = glob.glob(padrao)
        for arquivo in arquivos:
            try:
                os.remove(arquivo)
                contador += 1
            except Exception as e:
                print(f"⚠️ Não foi possível deletar {arquivo}: {e}")
    
    imprimir_status(f"{contador} arquivos de cache removidos.")

def atualizar_drivers():
    imprimir_status("Verificando integridade do Playwright...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])
        imprimir_status("Drivers de navegador atualizados/verificados.")
    except Exception as e:
        imprimir_status(f"❌ Erro ao atualizar Playwright: {e}")

if __name__ == "__main__":
    print("╔══════════════════════════════════════╗")
    print("║   R2 SYSTEM - PROTOCOLO DE REPARO    ║")
    print("╚══════════════════════════════════════╝")
    
    # 1. Limpeza de Arquivos (Fazemos antes de matar processos para garantir log)
    limpar_arquivos_temporarios()
    
    # 2. Atualização de Drivers
    atualizar_drivers()
    
    print("\n✅ Manutenção concluída.")
    print("⚠️  AVISO: Agora vou executar o 'taskkill'.")
    print("Isso vai fechar este terminal e qualquer python rodando.")
    input("Pressione ENTER para finalizar e matar os processos...")
    
    # 3. Mata tudo (inclusive este script)
    matar_processos_zumbis()