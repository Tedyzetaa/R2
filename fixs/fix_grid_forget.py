#!/usr/bin/env python3
"""
Script para corrigir o erro grid_forget no sci_fi_hud.py
Execute antes de iniciar o R2 Assistant
"""

import os
import sys
import re
from pathlib import Path

def fix_sci_fi_hud():
    """Corrige o arquivo sci_fi_hud.py"""
    
    hud_path = Path("gui/sci_fi_hud.py")
    backup_path = Path("gui/sci_fi_hud.py.backup")
    
    if not hud_path.exists():
        print("❌ Arquivo sci_fi_hud.py não encontrado")
        return False
    
    try:
        # Criar backup
        import shutil
        shutil.copy2(hud_path, backup_path)
        print(f"✅ Backup criado: {backup_path}")
        
        # Ler conteúdo
        with open(hud_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Remover todas as referências a grid_forget
        original_content = content
        
        # Padrões para remover
        patterns_to_remove = [
            r'\.grid_forget\(\)',
            r'\._safe_grid_forget\(\)',
            r'self\._safe_grid_forget\(\)',
            r'def _safe_grid_forget\(.*?\):.*?(?=\n\n|\n\w)',
        ]
        
        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        # 2. Substituir métodos problemáticos
        # Encontrar método _create_simple_interface
        method_pattern = r'def _create_simple_interface\(self\):(.*?)(?=\n\n|\n\w)'
        match = re.search(method_pattern, content, re.DOTALL)
        
        if match:
            old_method = match.group(0)
            new_method = '''def _create_simple_interface(self):
        """Interface simples de fallback - VERSÃO CORRIGIDA"""
        try:
            # Limpar widgets filhos de forma segura
            for widget in self.winfo_children():
                try:
                    widget.destroy()
                except:
                    pass
            
            # Configuração básica
            self.configure(fg_color="#0a0a12")
            
            # Criar interface básica
            self._create_basic_interface()
            
        except Exception as e:
            print(f"Erro na interface simples: {e}")
            # Continuar com a interface existente'''
            
            content = content.replace(old_method, new_method)
        
        # 3. Adicionar método auxiliar se não existir
        if '_create_basic_interface' not in content:
            basic_interface = '''
    def _create_basic_interface(self):
        """Cria interface básica de fallback"""
        try:
            import customtkinter as ctk
            
            # Frame principal
            main_frame = ctk.CTkFrame(self, fg_color="transparent")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Título
            title = ctk.CTkLabel(
                main_frame,
                text="R2 ASSISTANT - MODO RESCUE",
                font=("Courier", 24, "bold"),
                text_color="#00ffff"
            )
            title.pack(pady=20)
            
            # Mensagem de status
            status = ctk.CTkLabel(
                main_frame,
                text="Sistema operacional em modo de recuperação\\nInterface Sci-Fi desativada",
                font=("Arial", 12),
                text_color="#8888ff"
            )
            status.pack(pady=10)
            
            # Botão para continuar
            continue_btn = ctk.CTkButton(
                main_frame,
                text="Continuar",
                command=self._continue_with_basic,
                width=200
            )
            continue_btn.pack(pady=20)
            
        except Exception as e:
            print(f"Erro na interface básica: {e}")
    
    def _continue_with_basic(self):
        """Continua com interface básica"""
        for widget in self.winfo_children():
            widget.destroy()
        
        from start_r2_safe import SafeLauncher
        SafeLauncher.launch_basic_gui(self.config)'''
            
            # Inserir antes do final da classe
            class_end = content.find('\n\n', content.find('class R2SciFiGUI'))
            if class_end != -1:
                content = content[:class_end] + basic_interface + content[class_end:]
        
        # Escrever arquivo corrigido
        with open(hud_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ sci_fi_hud.py corrigido com sucesso!")
        
        # Verificar diferenças
        lines_removed = len(original_content.split('\n')) - len(content.split('\n'))
        print(f"📊 Linhas alteradas: ~{lines_removed}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir sci_fi_hud.py: {e}")
        import traceback
        traceback.print_exc()
        
        # Restaurar backup
        if backup_path.exists():
            shutil.copy2(backup_path, hud_path)
            print("🔄 Backup restaurado")
        
        return False

def create_safe_launcher():
    """Cria um launcher seguro que ignora problemas de GUI"""
    
    launcher_content = '''#!/usr/bin/env python3
"""
R2 Assistant - Launcher Seguro
Ignora problemas de GUI e usa modo básico
"""

import sys
import os
from pathlib import Path

# Adicionar diretório ao path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Desativar verificação de GUI problemática
os.environ["R2_NO_SCI_FI_GUI"] = "1"

# Importar e executar launcher seguro
from start_r2_safe import main

if __name__ == "__main__":
    sys.exit(main())
'''
    
    launcher_path = Path("launch_safe.py")
    launcher_path.write_text(launcher_content, encoding='utf-8')
    
    print(f"✅ Launcher seguro criado: {launcher_path}")
    return True

def main():
    """Função principal de correção"""
    
    print("\n" + "="*60)
    print("🔧 CORRIGINDO ERRO grid_forget")
    print("="*60)
    
    # 1. Corrigir sci_fi_hud.py
    print("\n1. Corrigindo sci_fi_hud.py...")
    if not fix_sci_fi_hud():
        print("⚠️  Continuando sem correção completa")
    
    # 2. Criar launcher seguro
    print("\n2. Criando launcher seguro...")
    create_safe_launcher()
    
    # 3. Verificar dependências
    print("\n3. Verificando dependências...")
    
    try:
        import customtkinter as ctk
        print("✅ CustomTkinter: OK")
    except ImportError as e:
        print(f"❌ CustomTkinter: {e}")
    
    try:
        import tkinter
        print("✅ tkinter: OK")
    except ImportError as e:
        print(f"❌ tkinter: {e}")
    
    # 4. Instruções
    print("\n" + "="*60)
    print("🎯 INSTRUÇÕES PARA USO:")
    print("="*60)
    print("\n1. Use o launcher seguro:")
    print("   python launch_safe.py")
    print("\n2. Ou use o script corrigido:")
    print("   python start_r2_safe.py")
    print("\n3. Se ainda houver problemas:")
    print("   python emergency_recovery.py")
    print("\n" + "="*60)
    
    return True

if __name__ == "__main__":
    main()