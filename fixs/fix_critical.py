"""
CORREÇÃO CRÍTICA DO R2 ASSISTANT
Script para corrigir todos os problemas de dependência e arquivos
"""
import os
import sys
import subprocess
import importlib
from pathlib import Path

def print_step(step, message):
    print(f"\n🔧 {step}. {message}")
    print("=" * 60)

def fix_numpy_matplotlib():
    """Corrige problemas com numpy e matplotlib"""
    print_step(1, "Corrigindo numpy e matplotlib...")
    
    try:
        # Forçar reinstalação limpa
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "numpy", "matplotlib", "-y", "--quiet"])
        
        # Instalar versões estáveis e comprovadas
        subprocess.run([sys.executable, "-m", "pip", "install", "numpy==1.24.3", "--quiet"])
        subprocess.run([sys.executable, "-m", "pip", "install", "matplotlib==3.7.1", "--quiet"])
        
        # Verificar instalação
        import numpy as np
        import matplotlib
        print(f"✅ Numpy: {np.__version__} | pi: {np.pi}")
        print(f"✅ Matplotlib: {matplotlib.__version__}")
        
        # Configurar backend seguro
        matplotlib.use('Agg')
        print("✅ Matplotlib backend configurado: 'Agg'")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
    return True

def fix_speech_recognition():
    """Instala SpeechRecognition"""
    print_step(2, "Instalando SpeechRecognition...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "SpeechRecognition", "--quiet"])
        
        import speech_recognition
        print("✅ SpeechRecognition instalado com sucesso")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("⚠️  Tente instalar manualmente: pip install SpeechRecognition")
        return False
    return True

def fix_wave_animation_file():
    """Corrige o arquivo wave_animation.py"""
    print_step(3, "Corrigindo wave_animation.py...")
    
    wave_file = Path("gui/components/wave_animation.py")
    
    if not wave_file.exists():
        print("❌ Arquivo não encontrado")
        return False
    
    try:
        with open(wave_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fazer backup
        backup_file = wave_file.with_suffix('.py.backup')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Substituir a linha problemática
        new_content = content.replace(
            'angle = (2 * np.pi * i / num_points) + self.angle',
            '            try:\n                angle = (2 * np.pi * i / num_points) + self.angle\n            except AttributeError:\n                import math\n                angle = (2 * math.pi * i / num_points) + self.angle'
        )
        
        # Substituir np.sin por math.sin
        new_content = new_content.replace(
            '            radius = self.size / 2 * (1 + 0.2 * np.sin(angle * 3 + self.angle))',
            '            try:\n                radius = self.size / 2 * (1 + 0.2 * np.sin(angle * 3 + self.angle))\n            except AttributeError:\n                import math\n                radius = self.size / 2 * (1 + 0.2 * math.sin(angle * 3 + self.angle))'
        )
        
        # Substituir np.cos e np.sin
        new_content = new_content.replace(
            '            x = radius * np.cos(angle)\n            y = radius * np.sin(angle)',
            '            try:\n                x = radius * np.cos(angle)\n                y = radius * np.sin(angle)\n            except AttributeError:\n                import math\n                x = radius * math.cos(angle)\n                y = radius * math.sin(angle)'
        )
        
        with open(wave_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Arquivo corrigido: {wave_file}")
        print(f"✅ Backup salvo em: {backup_file}")
        
    except Exception as e:
        print(f"❌ Erro ao corrigir arquivo: {e}")
        return False
    return True

def fix_sci_fi_hud_file():
    """Corrige o arquivo sci_fi_hud.py"""
    print_step(4, "Corrigindo sci_fi_hud.py...")
    
    hud_file = Path("gui/sci_fi_hud.py")
    
    if not hud_file.exists():
        print("❌ Arquivo não encontrado")
        return False
    
    try:
        with open(hud_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Fazer backup
        backup_file = hud_file.with_suffix('.py.backup')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        # Corrigir grid_forget (remover ou substituir)
        modified = False
        for i, line in enumerate(lines):
            if 'self.grid_forget()' in line:
                lines[i] = line.replace('self.grid_forget()', '# self.grid_forget() # REMOVIDO - causa erro')
                modified = True
        
        if modified:
            with open(hud_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"✅ grid_forget() removido de: {hud_file}")
        else:
            print("⚠️  grid_forget() não encontrado no arquivo")
        
        print(f"✅ Backup salvo em: {backup_file}")
        
    except Exception as e:
        print(f"❌ Erro ao corrigir arquivo: {e}")
        return False
    return True

def create_safe_startup_script():
    """Cria um script de inicialização seguro"""
    print_step(5, "Criando script de inicialização seguro...")
    
    script_content = '''
"""
R2 ASSISTANT - INICIALIZAÇÃO SEGURA
Script que inicia o R2 Assistant com verificações e fallbacks
"""
import sys
import os
from pathlib import Path

def check_dependencies():
    """Verifica dependências críticas"""
    print("🔍 Verificando dependências...")
    
    dependencies = {
        "customtkinter": "Interface gráfica",
        "numpy": "Cálculos matemáticos",
        "matplotlib": "Gráficos",
        "speech_recognition": "Reconhecimento de voz",
        "PIL": "Processamento de imagens (Pillow)",
        "requests": "Requisições HTTP",
        "psutil": "Monitoramento do sistema"
    }
    
    missing = []
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {description}")
        except ImportError:
            print(f"❌ {description}")
            missing.append(module)
    
    return len(missing) == 0

def start_safe_gui():
    """Inicia uma GUI segura com fallbacks"""
    print("🚀 Iniciando R2 Assistant em modo seguro...")
    
    try:
        import customtkinter as ctk
        from core.command_system import CommandSystem
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        class SafeR2GUI(ctk.CTk):
            def __init__(self):
                super().__init__()
                self.title("R2 Assistant - Modo Seguro")
                self.geometry("1000x700")
                self.cmd_system = CommandSystem()
                self.setup_ui()
            
            def setup_ui(self):
                # Frame principal
                self.main_frame = ctk.CTkFrame(self)
                self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
                
                # Cabeçalho
                header = ctk.CTkFrame(self.main_frame)
                header.pack(fill="x", pady=(0, 20))
                
                ctk.CTkLabel(
                    header,
                    text="🤖 R2 ASSISTANT - MODO SEGURO",
                    font=("Arial", 28, "bold"),
                    text_color="#00ffff"
                ).pack(pady=10)
                
                ctk.CTkLabel(
                    header,
                    text="✅ Sistema operacional com verificações ativas",
                    font=("Arial", 14)
                ).pack()
                
                # Console
                self.console = ctk.CTkTextbox(
                    self.main_frame,
                    height=400,
                    font=("Consolas", 12),
                    wrap="word"
                )
                self.console.pack(fill="both", expand=True, pady=(0, 15))
                self.console.insert("1.0", "R2 Assistant inicializado em modo seguro\\n\\n")
                
                # Sistema de comandos
                if self.cmd_system:
                    self.console.insert("end", f"✅ {len(self.cmd_system.commands)} comandos carregados\\n")
                
                # Entrada de comandos
                input_frame = ctk.CTkFrame(self.main_frame)
                input_frame.pack(fill="x")
                
                self.input_field = ctk.CTkEntry(
                    input_frame,
                    placeholder_text="Digite um comando...",
                    font=("Arial", 14),
                    height=40
                )
                self.input_field.pack(side="left", fill="x", expand=True, padx=(0, 10))
                self.input_field.bind("<Return>", lambda e: self.process_command())
                
                self.send_btn = ctk.CTkButton(
                    input_frame,
                    text="Enviar",
                    width=100,
                    height=40,
                    font=("Arial", 14),
                    command=self.process_command
                )
                self.send_btn.pack(side="right")
            
            def process_command(self, event=None):
                command = self.input_field.get().strip()
                if not command:
                    return
                
                self.console.insert("end", f"\\n> {command}\\n")
                
                try:
                    success, response = self.cmd_system.process_command(command)
                    if success:
                        self.console.insert("end", f"✅ {response}\\n")
                    else:
                        self.console.insert("end", f"⚠️  {response}\\n")
                except Exception as e:
                    self.console.insert("end", f"❌ Erro: {e}\\n")
                
                self.input_field.delete(0, "end")
                self.console.see("end")
        
        app = SafeR2GUI()
        app.mainloop()
        
    except Exception as e:
        print(f"❌ Erro na GUI segura: {e}")
        # Fallback para terminal
        print("🔄 Iniciando terminal interativo...")
        from core.command_system import CommandSystem
        cmd_system = CommandSystem()
        cmd_system.run_interactive()

def main():
    print("=" * 60)
    print("🤖 R2 ASSISTANT - INICIALIZAÇÃO SEGURA")
    print("=" * 60)
    
    # Verificar dependências
    if not check_dependencies():
        print("\\n⚠️  Algumas dependências estão faltando!")
        print("Execute: pip install customtkinter numpy matplotlib SpeechRecognition pillow requests psutil")
        response = input("Deseja tentar continuar mesmo assim? (S/N): ")
        if response.upper() != "S":
            return
    
    # Iniciar GUI segura
    start_safe_gui()

if __name__ == "__main__":
    main()
'''
    
    try:
        safe_file = Path("start_safe.py")
        with open(safe_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ Script criado: {safe_file}")
        print("Para usar: python start_safe.py")
        
    except Exception as e:
        print(f"❌ Erro ao criar script: {e}")
        return False
    return True

def main():
    print("=" * 70)
    print("🔧 CORREÇÃO COMPLETA DO R2 ASSISTANT")
    print("=" * 70)
    
    print("Este script vai corrigir todos os problemas conhecidos:")
    print("1. Numpy corrompido (atributo 'pi' faltando)")
    print("2. Matplotlib corrompido (atributo 'use' faltando)")
    print("3. SpeechRecognition não instalado")
    print("4. Erro grid_forget()")
    print("5. Criar script de inicialização seguro")
    print("=" * 70)
    
    response = input("Deseja continuar? (S/N): ")
    if response.upper() != "S":
        print("❌ Operação cancelada")
        return
    
    # Executar todas as correções
    success = True
    
    success = fix_numpy_matplotlib() and success
    success = fix_speech_recognition() and success
    success = fix_wave_animation_file() and success
    success = fix_sci_fi_hud_file() and success
    success = create_safe_startup_script() and success
    
    print("\n" + "=" * 70)
    if success:
        print("✅ TODAS AS CORREÇÕES CONCLUÍDAS COM SUCESSO!")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. Execute: python start_safe.py")
        print("2. Ou use o menu principal: python start_r2.py")
        print("3. Escolha a opção 1 para GUI Completa")
    else:
        print("⚠️  ALGUMAS CORREÇÕES FALHARAM!")
        print("Tente executar os comandos manualmente.")
    
    print("=" * 70)

if __name__ == "__main__":
    main()