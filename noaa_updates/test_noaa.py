#!/usr/bin/env python3
"""
Teste do módulo NOAA
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_noaa_service():
    """Testa o serviço NOAA"""
    print("=== Teste NOAA Service ===")
    
    try:
        from features.noaa.noaa_service import get_noaa_service
        
        service = get_noaa_service()
        print("[OK] NOAA Service importado")
        
        # Teste básico
        print("Configuração carregada:", service.config is not None)
        print("Endpoints configurados:", len(service.endpoints))
        
        return True
    except Exception as e:
        print(f"[ERRO] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_noaa_commands():
    """Testa comandos NOAA"""
    print("\n=== Teste NOAA Commands ===")
    
    try:
        from commands.noaa_commands import NOAACommands
        
        commands = NOAACommands(None)
        print(f"[OK] {len(commands.commands)} comandos NOAA carregados")
        
        # Listar comandos
        print("Comandos disponíveis:")
        for cmd_name, cmd_data in commands.commands.items():
            print(f"  - {cmd_name}: {cmd_data['description']}")
        
        return True
    except Exception as e:
        print(f"[ERRO] {e}")
        return False

def test_noaa_panel():
    """Testa painel NOAA"""
    print("\n=== Teste NOAA Panel ===")
    
    try:
        from gui.components.noaa_panel import NOAAPanel
        print("[OK] NOAA Panel importado")
        
        # Verificar se pode criar instância
        import customtkinter as ctk
        ctk.set_appearance_mode("dark")
        
        root = ctk.CTk()
        root.withdraw()  # Não mostrar janela
        
        panel = NOAAPanel(root)
        print("[OK] Painel NOAA criado com sucesso")
        
        info = panel.get_panel_info()
        print(f"Info: {info}")
        
        root.destroy()
        return True
    except Exception as e:
        print(f"[ERRO] {e}")
        return False

async def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do módulo NOAA...")
    
    results = []
    
    # Testar serviço
    results.append(await test_noaa_service())
    
    # Testar comandos
    results.append(test_noaa_commands())
    
    # Testar painel
    results.append(test_noaa_panel())
    
    # Resumo
    print("\n=== RESUMO DOS TESTES ===")
    for i, (test_name, result) in enumerate([
        ("NOAA Service", results[0]),
        ("NOAA Commands", results[1]),
        ("NOAA Panel", results[2])
    ]):
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:20} {status}")
    
    if all(results):
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        return 0
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM")
        return 1

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
